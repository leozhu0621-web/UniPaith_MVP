from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.ai_runtime_metrics import record_self_driving, start_timer
from unipaith.ml.model_manager import ModelManager
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.institution import Program
from unipaith.models.matching import (
    DataSource,
    Embedding,
    InstitutionFeature,
    MatchResult,
    ModelRegistry,
    PredictionLog,
)
from unipaith.models.ml_loop import DriftSnapshot, EvaluationRun, OutcomeRecord, TrainingRun
from unipaith.services.ai_engine_orchestrator import AIEngineOrchestrator

logger = logging.getLogger("unipaith.ai_control_plane")


_runtime_policy: dict[str, Any] = {
    "autonomy_enabled": settings.ai_autonomy_enabled,
    "auto_fix_enabled": settings.ai_autonomy_auto_fix,
    "emergency_stop": settings.ai_autonomy_emergency_stop,
    "max_consecutive_failures": settings.ai_autonomy_max_consecutive_failures,
}

_runtime_loop_state: dict[str, Any] = {
    "last_tick_at": None,
    "last_tick_status": "never_run",
    "last_tick_summary": None,
    "last_tick_phase_summary": None,
    "current_phase": None,
    "phase_started_at": None,
    "consecutive_failures": 0,
}

_autonomy_audit_events: list[dict[str, Any]] = []


class AIControlPlaneService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_status(self) -> dict[str, Any]:
        scheduler_effective_enabled = settings.scheduler_enabled or (
            settings.scheduler_auto_enable_non_test and settings.environment != "test"
        )
        active_sources = await self.db.scalar(
            select(func.count()).select_from(DataSource).where(DataSource.is_active.is_(True))
        )
        programs_in_db = await self.db.scalar(select(func.count()).select_from(Program))
        features_generated = await self.db.scalar(
            select(func.count()).select_from(InstitutionFeature)
        )
        embeddings_generated = await self.db.scalar(select(func.count()).select_from(Embedding))

        recent_crawl_failures = await self.db.scalar(
            select(func.count()).select_from(CrawlJob).where(CrawlJob.status == "failed")
        )
        recent_training_failures = await self.db.scalar(
            select(func.count()).select_from(TrainingRun).where(TrainingRun.status == "failed")
        )
        total_predictions = await self.db.scalar(select(func.count()).select_from(PredictionLog))
        stale_matches = await self.db.scalar(
            select(func.count()).select_from(MatchResult).where(MatchResult.is_stale.is_(True))
        )

        latest_drift = await self.db.execute(
            select(DriftSnapshot).order_by(DriftSnapshot.created_at.desc()).limit(1)
        )
        latest_eval = await self.db.execute(
            select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(1)
        )
        latest_train = await self.db.execute(
            select(TrainingRun).order_by(TrainingRun.created_at.desc()).limit(1)
        )
        latest_crawl = await self.db.execute(
            select(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(1)
        )
        latest_extracted = await self.db.execute(
            select(ExtractedProgram).order_by(ExtractedProgram.created_at.desc()).limit(1)
        )

        return {
            "policy": dict(_runtime_policy),
            "scheduler": {
                "enabled": scheduler_effective_enabled,
                "configured_enabled": settings.scheduler_enabled,
                "self_driving_enabled": settings.scheduler_self_driving_enabled,
                "self_driving_interval_minutes": settings.scheduler_self_driving_interval_minutes,
                "leader_only_mode": settings.scheduler_require_leader,
            },
            "llm": {
                "provider": self._runtime_provider(),
                "runtime_mode": settings.gpu_mode,
                "base_url": settings.llm_reasoning_base_url,
                "feature_model": settings.llm_feature_model,
                "reasoning_model": settings.llm_reasoning_model,
                "embedding_model": settings.embedding_model,
                "api_key_configured": bool(settings.openai_api_key),
                "runtime_split": {
                    "llm": self._runtime_provider(),
                    "embedding": self._runtime_provider(),
                },
            },
            "engine": {
                "active_sources": int(active_sources or 0),
                "programs_in_db": int(programs_in_db or 0),
                "features_generated": int(features_generated or 0),
                "embeddings_generated": int(embeddings_generated or 0),
                "engine_ready": bool(embeddings_generated and embeddings_generated > 0),
            },
            "ml_policy": {
                "eval_retrain_min_new_outcomes": settings.eval_retrain_min_new_outcomes,
                "eval_retrain_max_hours_without_training": (
                    settings.eval_retrain_max_hours_without_training
                ),
                "training_default_cycle_mode": settings.training_default_cycle_mode,
                "training_default_manual_mode": settings.training_default_manual_mode,
                "training_degraded_mode_failure_rate_threshold": (
                    settings.training_degraded_mode_failure_rate_threshold
                ),
                "training_degraded_mode_min_runs": settings.training_degraded_mode_min_runs,
            },
            "reliability": {
                "crawl_failures_total": int(recent_crawl_failures or 0),
                "training_failures_total": int(recent_training_failures or 0),
                "consecutive_autonomy_failures": int(
                    _runtime_loop_state["consecutive_failures"] or 0
                ),
                "predictions_logged_total": int(total_predictions or 0),
                "stale_matches": int(stale_matches or 0),
            },
            "latest_runs": {
                "drift": self._serialize_row(latest_drift.scalar_one_or_none(), "drift"),
                "evaluation": self._serialize_row(latest_eval.scalar_one_or_none(), "evaluation"),
                "training": self._serialize_row(latest_train.scalar_one_or_none(), "training"),
                "crawl": self._serialize_row(latest_crawl.scalar_one_or_none(), "crawl"),
                "extracted_program": self._serialize_row(
                    latest_extracted.scalar_one_or_none(), "extracted_program"
                ),
            },
            "autonomy_loop": dict(_runtime_loop_state),
            "engine_runtime": AIEngineOrchestrator(self.db).get_runtime_state(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def update_policy(
        self,
        autonomy_enabled: bool | None = None,
        auto_fix_enabled: bool | None = None,
        emergency_stop: bool | None = None,
    ) -> dict[str, Any]:
        if autonomy_enabled is not None:
            _runtime_policy["autonomy_enabled"] = autonomy_enabled
        if auto_fix_enabled is not None:
            _runtime_policy["auto_fix_enabled"] = auto_fix_enabled
        if emergency_stop is not None:
            _runtime_policy["emergency_stop"] = emergency_stop
        return dict(_runtime_policy)

    async def run_self_driving_tick(self, trigger: str = "manual") -> dict[str, Any]:
        timer = start_timer()
        started_at = datetime.now(UTC)
        phase_summary: dict[str, dict[str, Any]] = {
            "detect": {"status": "pending", "started_at": None, "completed_at": None},
            "diagnose": {"status": "pending", "started_at": None, "completed_at": None},
            "remediate": {"status": "pending", "started_at": None, "completed_at": None},
            "verify": {"status": "pending", "started_at": None, "completed_at": None},
            "rollback": {"status": "pending", "started_at": None, "completed_at": None},
        }

        if _runtime_policy.get("emergency_stop"):
            summary = {
                "trigger": trigger,
                "status": "skipped",
                "reason": "emergency_stop_enabled",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
                "phase_summary": phase_summary,
            }
            self._record_tick(summary)
            return summary

        if not _runtime_policy.get("autonomy_enabled"):
            summary = {
                "trigger": trigger,
                "status": "skipped",
                "reason": "autonomy_disabled",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
                "phase_summary": phase_summary,
            }
            self._record_tick(summary)
            return summary

        try:
            self._begin_phase("detect", phase_summary)
            anomalies = await self._detect_anomalies()
            self._complete_phase("detect", phase_summary, "ok")

            self._begin_phase("diagnose", phase_summary)
            diagnosis = self._diagnose(anomalies)
            self._complete_phase("diagnose", phase_summary, "ok")

            self._begin_phase("remediate", phase_summary)
            remediation = await self._remediate(diagnosis, trigger)
            self._complete_phase(
                "remediate",
                phase_summary,
                "ok" if remediation.get("status") == "ok" else "error",
            )

            self._begin_phase("verify", phase_summary)
            verification = await self._verify(remediation)
            self._complete_phase(
                "verify",
                phase_summary,
                "ok" if verification.get("status") == "ok" else "error",
            )

            rollback = None
            if verification["status"] != "ok":
                self._begin_phase("rollback", phase_summary)
                rollback = await self._rollback(remediation)
                self._complete_phase(
                    "rollback",
                    phase_summary,
                    "ok" if rollback.get("status") == "ok" else "error",
                )
            else:
                phase_summary["rollback"]["status"] = "skipped"
            completed_at = datetime.now(UTC)
            summary = {
                "trigger": trigger,
                "status": "ok" if verification["status"] == "ok" else "degraded",
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "anomalies": anomalies,
                "diagnosis": diagnosis,
                "remediation": remediation,
                "verification": verification,
                "rollback": rollback,
                "phase_summary": phase_summary,
            }
            if summary["status"] == "ok":
                _runtime_loop_state["consecutive_failures"] = 0
            else:
                _runtime_loop_state["consecutive_failures"] = (
                    int(_runtime_loop_state.get("consecutive_failures", 0)) + 1
                )
            self._record_tick(summary)
            self._append_audit("self_driving_tick", summary)
            record_self_driving(timer, ok=summary["status"] == "ok")
            return summary
        except Exception as exc:  # pragma: no cover - safety path
            logger.exception("Self-driving tick failed")
            current_phase = _runtime_loop_state.get("current_phase")
            if current_phase and current_phase in phase_summary:
                self._complete_phase(current_phase, phase_summary, "error")
            _runtime_loop_state["consecutive_failures"] = (
                int(_runtime_loop_state.get("consecutive_failures", 0)) + 1
            )
            if _runtime_loop_state["consecutive_failures"] >= int(
                _runtime_policy["max_consecutive_failures"]
            ):
                _runtime_policy["emergency_stop"] = True
                logger.error("Emergency stop activated due to repeated self-driving failures")
            summary = {
                "trigger": trigger,
                "status": "error",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(UTC).isoformat(),
                "error": str(exc),
                "consecutive_failures": _runtime_loop_state["consecutive_failures"],
                "emergency_stop": _runtime_policy["emergency_stop"],
                "phase_summary": phase_summary,
            }
            self._record_tick(summary)
            self._append_audit("self_driving_tick_error", summary)
            record_self_driving(timer, ok=False)
            return summary

    async def list_audit_events(self, limit: int = 200) -> list[dict[str, Any]]:
        if limit < 1:
            return []
        return list(_autonomy_audit_events[-limit:])

    def _record_tick(self, summary: dict[str, Any]) -> None:
        _runtime_loop_state["last_tick_at"] = summary.get("completed_at")
        _runtime_loop_state["last_tick_status"] = summary.get("status")
        _runtime_loop_state["last_tick_summary"] = summary
        _runtime_loop_state["last_tick_phase_summary"] = summary.get("phase_summary")
        _runtime_loop_state["current_phase"] = None
        _runtime_loop_state["phase_started_at"] = None

    def _begin_phase(self, phase_name: str, phase_summary: dict[str, dict[str, Any]]) -> None:
        now = datetime.now(UTC).isoformat()
        _runtime_loop_state["current_phase"] = phase_name
        _runtime_loop_state["phase_started_at"] = now
        phase_summary[phase_name]["started_at"] = now
        phase_summary[phase_name]["status"] = "running"

    def _complete_phase(
        self,
        phase_name: str,
        phase_summary: dict[str, dict[str, Any]],
        status: str,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        phase_summary[phase_name]["completed_at"] = now
        phase_summary[phase_name]["status"] = status
        _runtime_loop_state["current_phase"] = None
        _runtime_loop_state["phase_started_at"] = None

    def _append_audit(self, event_type: str, payload: dict[str, Any]) -> None:
        _autonomy_audit_events.append(
            {
                "event_type": event_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            }
        )
        if len(_autonomy_audit_events) > 1000:
            del _autonomy_audit_events[: len(_autonomy_audit_events) - 1000]

    async def _detect_anomalies(self) -> dict[str, Any]:
        recent_failed_crawls = await self.db.scalar(
            select(func.count()).select_from(CrawlJob).where(CrawlJob.status == "failed")
        )
        latest_drift_row = await self.db.execute(
            select(DriftSnapshot).order_by(DriftSnapshot.created_at.desc()).limit(1)
        )
        latest_drift = latest_drift_row.scalar_one_or_none()

        stale_matches = await self.db.scalar(
            select(func.count()).select_from(MatchResult).where(MatchResult.is_stale.is_(True))
        )
        has_embedding = await self.db.scalar(select(func.count()).select_from(Embedding))

        return {
            "crawl_failures_total": int(recent_failed_crawls or 0),
            "latest_drift_detected": bool(latest_drift.drift_detected) if latest_drift else False,
            "stale_matches": int(stale_matches or 0),
            "embedding_count": int(has_embedding or 0),
        }

    def _diagnose(self, anomalies: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        if anomalies["embedding_count"] == 0:
            issues.append("embeddings_missing")
        if anomalies["latest_drift_detected"]:
            issues.append("drift_detected")
        if anomalies["stale_matches"] > 100:
            issues.append("match_cache_stale")
        if anomalies["crawl_failures_total"] > 5:
            issues.append("crawl_pipeline_unstable")

        severity = "low"
        if "embeddings_missing" in issues or "drift_detected" in issues:
            severity = "high"
        elif issues:
            severity = "medium"

        return {"issues": issues, "severity": severity}

    async def _remediate(self, diagnosis: dict[str, Any], trigger: str) -> dict[str, Any]:
        actions: list[dict[str, Any]] = []
        issues = diagnosis.get("issues", [])

        if not issues:
            return {"status": "ok", "actions": actions, "note": "no_issues_detected"}

        if "crawl_pipeline_unstable" in issues or "embeddings_missing" in issues:
            ingest = await AIEngineOrchestrator(self.db).run_ingest_phase()
            actions.append({"action": "run_ingest_phase", "result": ingest})
            feat = await AIEngineOrchestrator(self.db).run_feature_embedding_phase()
            actions.append({"action": "run_feature_embedding_phase", "result": feat})

        if "drift_detected" in issues or "match_cache_stale" in issues:
            ml = await AIEngineOrchestrator(self.db).run_ml_phase(
                trigger=f"auto-remediate:{trigger}"
            )
            actions.append({"action": "run_ml_phase", "result": ml})

        status = "ok"
        if any(a["result"].get("status") == "error" for a in actions):
            status = "error"
        return {"status": status, "actions": actions}

    async def _verify(self, remediation: dict[str, Any]) -> dict[str, Any]:
        """Post-remediation health check; tolerant of failed training when stack can still serve."""
        embedding_count = await self.db.scalar(select(func.count()).select_from(Embedding))
        embeddings_ok = bool((embedding_count or 0) > 0)

        latest_train = await self.db.execute(
            select(TrainingRun).order_by(TrainingRun.created_at.desc()).limit(1)
        )
        latest_train_obj = latest_train.scalar_one_or_none()
        latest_failed = bool(latest_train_obj is not None and latest_train_obj.status == "failed")

        active_row = await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.is_active.is_(True)).limit(1)
        )
        has_active_model = active_row.scalar_one_or_none() is not None

        training_gate_ok = not latest_failed or has_active_model or embeddings_ok

        checks = {
            "embeddings_present": embeddings_ok,
            "latest_training_not_failed": not latest_failed,
            "training_gate_ok": training_gate_ok,
            "has_active_model": has_active_model,
        }
        base_ok = embeddings_ok and training_gate_ok and remediation.get("status") != "error"
        status = "ok" if base_ok else "error"
        return {"status": status, "checks": checks}

    async def _rollback(self, remediation: dict[str, Any]) -> dict[str, Any]:
        ml_attempted = any(
            a.get("action") == "run_ml_phase" for a in remediation.get("actions", [])
        )
        if not ml_attempted:
            return {"status": "skipped", "reason": "no_ml_change_to_rollback"}

        try:
            rollback = await ModelManager(self.db).rollback_model()
            return {"status": "ok", "result": rollback}
        except Exception as exc:
            logger.exception("Rollback failed during self-driving verification")
            return {"status": "error", "error": str(exc)}

    def _serialize_row(self, row: Any, row_type: str) -> dict[str, Any] | None:
        if row is None:
            return None
        if row_type == "drift":
            return {
                "id": str(row.id),
                "drift_detected": row.drift_detected,
                "snapshot_type": row.snapshot_type,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        if row_type == "evaluation":
            return {
                "id": str(row.id),
                "model_version": row.model_version,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        if row_type == "training":
            return {
                "id": str(row.id),
                "status": row.status,
                "resulting_model_version": row.resulting_model_version,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        if row_type == "crawl":
            return {
                "id": str(row.id),
                "status": row.status,
                "items_extracted": row.items_extracted,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            }
        if row_type == "extracted_program":
            return {
                "id": str(row.id),
                "institution_name": row.institution_name,
                "program_name": row.program_name,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        return None

    async def get_ops_snapshot(self) -> dict[str, Any]:
        """Consolidated payload for the admin AI Operations Center."""
        status = await self.get_status()
        now = datetime.now(UTC).isoformat()

        active_crawl_jobs = await self.db.scalar(
            select(func.count())
            .select_from(CrawlJob)
            .where(CrawlJob.status.in_(["pending", "running"]))
        )
        pending_review = await self.db.scalar(
            select(func.count())
            .select_from(ExtractedProgram)
            .where(ExtractedProgram.review_status == "pending")
        )
        active_model = await self.db.execute(
            select(ModelRegistry)
            .where(ModelRegistry.is_active.is_(True))
            .order_by(ModelRegistry.promoted_at.desc())
            .limit(1)
        )
        active_model_row = active_model.scalar_one_or_none()

        return {
            "timestamp": now,
            "status": status,
            "processing": {
                "engine": status.get("engine_runtime"),
                "autonomy_loop": status.get("autonomy_loop"),
                "latest_runs": status.get("latest_runs"),
            },
            "crawler": {
                "active_sources": status.get("engine", {}).get("active_sources", 0),
                "active_jobs": int(active_crawl_jobs or 0),
                "pending_review_items": int(pending_review or 0),
                "latest_crawl": status.get("latest_runs", {}).get("crawl"),
            },
            "ml": {
                "active_model": {
                    "model_version": active_model_row.model_version if active_model_row else None,
                    "promoted_at": (
                        active_model_row.promoted_at.isoformat()
                        if active_model_row and active_model_row.promoted_at
                        else None
                    ),
                },
                "latest_training": status.get("latest_runs", {}).get("training"),
                "latest_evaluation": status.get("latest_runs", {}).get("evaluation"),
                "latest_drift": status.get("latest_runs", {}).get("drift"),
            },
            "reliability": status.get("reliability"),
            "audit_preview": (await self.list_audit_events(limit=20)),
        }

    async def get_architecture_trace(
        self,
        include_runs: bool = True,
        limit: int = 20,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        status = await self.get_status()

        latest_outcome_row = await self.db.execute(
            select(OutcomeRecord).order_by(OutcomeRecord.outcome_recorded_at.desc()).limit(1)
        )
        latest_outcome = latest_outcome_row.scalar_one_or_none()
        latest_prediction_at = await self.db.scalar(select(func.max(PredictionLog.predicted_at)))

        active_model_row = await self.db.execute(
            select(ModelRegistry)
            .where(ModelRegistry.is_active.is_(True))
            .order_by(ModelRegistry.promoted_at.desc())
            .limit(1)
        )
        active_model = active_model_row.scalar_one_or_none()
        latest_model_event_row = await self.db.execute(
            select(ModelRegistry)
            .where(
                (ModelRegistry.promoted_at.is_not(None)) | (ModelRegistry.retired_at.is_not(None))
            )
            .order_by(func.coalesce(ModelRegistry.promoted_at, ModelRegistry.retired_at).desc())
            .limit(1)
        )
        latest_model_event = latest_model_event_row.scalar_one_or_none()

        latest_runs = status.get("latest_runs", {})
        crawl_latest = latest_runs.get("crawl") or {}
        drift_latest = latest_runs.get("drift") or {}
        eval_latest = latest_runs.get("evaluation") or {}
        training_latest = latest_runs.get("training") or {}
        engine_runtime = status.get("engine_runtime", {})
        reliability = status.get("reliability", {})
        ml_policy = status.get("ml_policy", {})

        stage_rows: list[dict[str, Any]] = [
            {
                "stage_id": "ingest",
                "label": "Ingest",
                "status": self._status_from_value(
                    crawl_latest.get("status"),
                    ok_values={"completed", "ok"},
                    warn_values={"running", "pending"},
                ),
                "last_run_at": self._safe_dt(
                    crawl_latest.get("completed_at") or crawl_latest.get("created_at"),
                ),
                "duration_ms": self._safe_num(
                    engine_runtime.get("last_stage_durations_ms", {}).get("ingest")
                ),
                "counts": {
                    "active_sources": status.get("engine", {}).get("active_sources"),
                    "active_jobs": status.get("engine", {}).get("active_jobs")
                    if "active_jobs" in status.get("engine", {})
                    else None,
                    "items_extracted": crawl_latest.get("items_extracted"),
                    "job_created_at": crawl_latest.get("created_at"),
                },
                "error": None
                if reliability.get("crawl_failures_total", 0) == 0
                else "recent_crawl_failures_detected",
                "source": "crawler_jobs",
            },
            {
                "stage_id": "understand",
                "label": "LLM Understand",
                "status": "ok"
                if status.get("engine", {}).get("features_generated", 0)
                and status.get("engine", {}).get("embeddings_generated", 0)
                else "warning",
                "last_run_at": self._safe_dt(engine_runtime.get("last_run_completed_at")),
                "duration_ms": self._safe_num(
                    engine_runtime.get("last_stage_durations_ms", {}).get("feature_embedding")
                ),
                "counts": {
                    "features_generated": status.get("engine", {}).get("features_generated"),
                    "embeddings_generated": status.get("engine", {}).get("embeddings_generated"),
                    "runtime_provider": status.get("llm", {}).get("provider"),
                },
                "error": None,
                "source": "feature_embedding_pipeline",
            },
            {
                "stage_id": "match",
                "label": "Matching",
                "status": "ok" if reliability.get("predictions_logged_total", 0) > 0 else "warning",
                "last_run_at": self._safe_dt(latest_prediction_at),
                "duration_ms": self._safe_num(
                    engine_runtime.get("last_stage_durations_ms", {}).get("ml")
                ),
                "counts": {
                    "predictions_logged_total": reliability.get("predictions_logged_total"),
                    "stale_matches": reliability.get("stale_matches"),
                },
                "error": None,
                "source": "prediction_logs",
            },
            {
                "stage_id": "outcome",
                "label": "Outcome Capture",
                "status": "ok" if latest_outcome else "warning",
                "last_run_at": latest_outcome.outcome_recorded_at if latest_outcome else None,
                "duration_ms": None,
                "counts": {
                    "latest_outcome_source": latest_outcome.outcome_source
                    if latest_outcome
                    else None,
                    "latest_outcome_value": latest_outcome.actual_outcome
                    if latest_outcome
                    else None,
                },
                "error": None if latest_outcome else "no_outcomes_recorded",
                "source": "outcome_records",
            },
            {
                "stage_id": "evaluation",
                "label": "Evaluation/Drift/Fairness",
                "status": (
                    "warning"
                    if drift_latest.get("drift_detected")
                    else "ok"
                    if eval_latest
                    else "idle"
                ),
                "last_run_at": self._safe_dt(eval_latest.get("created_at")),
                "duration_ms": None,
                "counts": {
                    "drift_detected": drift_latest.get("drift_detected"),
                },
                "error": None,
                "source": "evaluation_runs_and_drift",
            },
            {
                "stage_id": "training",
                "label": "Training",
                "status": self._status_from_value(
                    training_latest.get("status"),
                    ok_values={"completed", "ok"},
                    warn_values={"running", "pending"},
                ),
                "last_run_at": self._safe_dt(training_latest.get("created_at")),
                "duration_ms": None,
                "counts": {
                    "mode_default_cycle": ml_policy.get("training_default_cycle_mode"),
                    "mode_default_manual": ml_policy.get("training_default_manual_mode"),
                },
                "error": training_latest.get("failure_reason"),
                "source": "training_runs",
            },
            {
                "stage_id": "promotion",
                "label": "Promotion/Rollback",
                "status": "ok" if active_model else "warning",
                "last_run_at": (
                    latest_model_event.promoted_at
                    if latest_model_event and latest_model_event.promoted_at
                    else latest_model_event.retired_at
                    if latest_model_event
                    else None
                ),
                "duration_ms": None,
                "counts": {
                    "active_model_version": active_model.model_version if active_model else None,
                    "latest_promoted_version": latest_model_event.model_version
                    if latest_model_event
                    else None,
                },
                "error": None if active_model else "no_active_model",
                "source": "model_registry",
            },
        ]

        runs: list[dict[str, Any]] = []
        if include_runs:
            runs.extend(await self._collect_training_run_traces(limit))
            runs.extend(await self._collect_evaluation_run_traces(limit))
            runs.extend(await self._collect_crawl_run_traces(limit))
            runs.extend(self._collect_engine_runtime_trace(engine_runtime))
            runs.sort(key=lambda r: r.get("started_at") or "", reverse=True)
            runs = runs[:limit]

        return {
            "generated_at": now.isoformat(),
            "stages": stage_rows,
            "runs": runs,
        }

    async def _collect_training_run_traces(self, limit: int) -> list[dict[str, Any]]:
        rows = (
            (
                await self.db.execute(
                    select(TrainingRun).order_by(TrainingRun.started_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        traces: list[dict[str, Any]] = []
        for row in rows:
            traces.append(
                {
                    "run_id": str(row.id),
                    "run_type": "training",
                    "status": self._status_from_value(
                        row.status, {"completed", "ok"}, {"running", "pending"}
                    ),
                    "started_at": row.started_at.isoformat() if row.started_at else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "duration_ms": self._duration_ms(row.started_at, row.completed_at),
                    "stage_id": "training",
                    "mode": row.mode,
                    "trigger_reason": row.trigger_reason,
                    "metrics": {
                        "new_outcomes_count": row.new_outcomes_count,
                        "resulting_model_version": row.resulting_model_version,
                        "status": row.status,
                    },
                    "links": {"kpi": "/admin/ml/kpis", "health": "/admin/ml/cycle/health"},
                }
            )
        return traces

    async def _collect_evaluation_run_traces(self, limit: int) -> list[dict[str, Any]]:
        rows = (
            (
                await self.db.execute(
                    select(EvaluationRun).order_by(EvaluationRun.started_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        traces: list[dict[str, Any]] = []
        for row in rows:
            traces.append(
                {
                    "run_id": str(row.id),
                    "run_type": "evaluation",
                    "status": "warning" if row.drift_detected else "ok",
                    "started_at": row.started_at.isoformat() if row.started_at else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "duration_ms": self._duration_ms(row.started_at, row.completed_at),
                    "stage_id": "evaluation",
                    "mode": None,
                    "trigger_reason": "retraining_triggered"
                    if row.retraining_triggered
                    else "no_retraining",
                    "metrics": {
                        "dataset_size": row.dataset_size,
                        "model_version": row.model_version,
                        "drift_detected": row.drift_detected,
                    },
                    "links": {"trend": "/admin/ml/trends", "health": "/admin/ml/cycle/health"},
                }
            )
        return traces

    async def _collect_crawl_run_traces(self, limit: int) -> list[dict[str, Any]]:
        rows = (
            (
                await self.db.execute(
                    select(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        traces: list[dict[str, Any]] = []
        for row in rows:
            traces.append(
                {
                    "run_id": str(row.id),
                    "run_type": "crawler",
                    "status": self._status_from_value(
                        row.status, {"completed", "ok"}, {"running", "pending"}
                    ),
                    "started_at": row.created_at.isoformat() if row.created_at else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "duration_ms": self._duration_ms(row.created_at, row.completed_at),
                    "stage_id": "ingest",
                    "mode": None,
                    "trigger_reason": row.status,
                    "metrics": {
                        "pages_crawled": row.pages_crawled,
                        "items_extracted": row.items_extracted,
                        "items_ingested": row.items_ingested,
                    },
                    "links": {"smoke": "/admin/ml/scheduler/smoke"},
                }
            )
        return traces

    def _collect_engine_runtime_trace(self, engine_runtime: dict[str, Any]) -> list[dict[str, Any]]:
        if not engine_runtime:
            return []
        return [
            {
                "run_id": "engine-runtime-latest",
                "run_type": "engine",
                "status": self._status_from_value(
                    engine_runtime.get("status"),
                    {"ok", "completed", "idle"},
                    {"running", "pending"},
                ),
                "started_at": engine_runtime.get("last_run_started_at"),
                "completed_at": engine_runtime.get("last_run_completed_at"),
                "duration_ms": None,
                "stage_id": "ingest",
                "mode": None,
                "trigger_reason": "engine_orchestrator",
                "metrics": {
                    "current_stage": engine_runtime.get("current_stage"),
                    "last_stage_statuses": engine_runtime.get("last_stage_statuses"),
                    "last_stage_durations_ms": engine_runtime.get("last_stage_durations_ms"),
                },
                "links": {"health": "/admin/ml/cycle/health"},
            }
        ]

    @staticmethod
    def _duration_ms(started_at: datetime | None, completed_at: datetime | None) -> float | None:
        if not started_at or not completed_at:
            return None
        return round((completed_at - started_at).total_seconds() * 1000, 2)

    @staticmethod
    def _safe_num(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _safe_dt(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None
        return None

    @staticmethod
    def _status_from_value(
        value: Any,
        ok_values: set[str] | None = None,
        warn_values: set[str] | None = None,
    ) -> str:
        if value is None:
            return "idle"
        normalized = str(value).lower()
        ok_values = ok_values or {"ok", "healthy", "ready", "completed"}
        warn_values = warn_values or {"running", "pending", "degraded", "warning"}
        if normalized in ok_values:
            return "ok"
        if normalized in warn_values:
            return "warning"
        return "error"

    @staticmethod
    def _runtime_provider() -> str:
        mode = (settings.gpu_mode or "").lower()
        if mode in {"mock"} or settings.ai_mock_mode:
            return "mock"
        if mode == "aws":
            return "aws"
        if mode in {"openai", "local"}:
            return "openai"
        return "openai"
