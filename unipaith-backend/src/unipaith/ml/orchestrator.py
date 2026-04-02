"""
MLOrchestrator — Coordinates the full self-improving ML cycle.

Runs evaluation, drift detection, retraining, fairness checking, and
model promotion in sequence.  Designed to be called by the admin API
or a scheduled job.  Never raises — always returns partial results.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.ai_runtime_metrics import record_ml_evaluation, start_timer
from unipaith.ml.ab_testing import ABTestManager
from unipaith.ml.drift_detector import DriftDetector
from unipaith.ml.evaluator import ModelEvaluator
from unipaith.ml.fairness import FairnessChecker
from unipaith.ml.model_manager import ModelManager
from unipaith.ml.outcome_collector import OutcomeCollector
from unipaith.ml.trainer import ModelTrainer
from unipaith.models.ml_loop import OutcomeRecord, TrainingRun

logger = logging.getLogger(__name__)


class MLOrchestrator:
    """End-to-end ML loop coordinator."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.evaluator = ModelEvaluator(db)
        self.drift_detector = DriftDetector(db)
        self.fairness_checker = FairnessChecker(db)
        self.trainer = ModelTrainer(db)
        self.model_manager = ModelManager(db)

    # ------------------------------------------------------------------
    # Full cycle
    # ------------------------------------------------------------------

    async def run_full_cycle(
        self,
        triggered_by: str = "scheduled",
        preferred_mode: str | None = None,
    ) -> dict[str, Any]:
        """Run the complete ML improvement cycle.

        Steps:
        1. Evaluate current model
        2. Check for data / prediction drift
        3. Retrain if evaluation or drift warrants it
        4. Run fairness checks on the new model
        5. Auto-promote if the new model is better

        Never raises — partial results are returned on failure.
        """
        started_at = datetime.now(timezone.utc)
        result: dict[str, Any] = {
            "started_at": started_at.isoformat(),
            "completed_at": None,
            "decision": None,
            "evaluation": None,
            "drift": None,
            "training": None,
            "fairness": None,
            "promotion": None,
        }

        # --- Step 1: Evaluation ---
        eval_timer = start_timer()
        try:
            eval_run = await self.evaluator.run_evaluation(
                evaluation_type="triggered",
            )
            record_ml_evaluation(eval_timer, ok=True)
            result["evaluation"] = {
                "id": str(eval_run.id),
                "model_version": eval_run.model_version,
                "dataset_size": eval_run.dataset_size,
                "metrics": eval_run.metrics,
                "retraining_triggered": eval_run.retraining_triggered,
                "drift_detected": eval_run.drift_detected,
            }
        except Exception:
            record_ml_evaluation(eval_timer, ok=False)
            logger.exception("Full cycle: evaluation step failed")
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            return result

        # --- Step 2: Drift detection ---
        try:
            drift_snapshots = await self.drift_detector.check_all_drift()
            any_drift = any(s.drift_detected for s in drift_snapshots)
            result["drift"] = {
                "snapshots_count": len(drift_snapshots),
                "drift_detected": any_drift,
                "details": [
                    {
                        "id": str(s.id),
                        "snapshot_type": s.snapshot_type,
                        "feature_name": s.feature_name,
                        "drift_detected": s.drift_detected,
                        "p_value": s.p_value,
                    }
                    for s in drift_snapshots
                ],
            }
        except Exception:
            logger.exception("Full cycle: drift detection step failed")
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            return result

        # --- Step 3: Determine if retraining is needed ---
        decision = await self._build_training_decision(
            eval_run=eval_run,
            any_drift=any_drift,
            triggered_by=triggered_by,
            preferred_mode=preferred_mode,
        )
        result["decision"] = decision
        training_needed = decision["training_needed"]
        if not training_needed:
            result["training"] = {"skipped": True, "reason": decision["skip_reason"]}
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            return result

        # --- Step 4: Run training ---
        try:
            training_mode = decision["training_mode"]
            training_run = await self.trainer.run_training(
                triggered_by=triggered_by,
                evaluation_run_id=eval_run.id,
                mode=training_mode,
                trigger_reason=decision["trigger_reason"],
                new_outcomes_count=decision["new_outcomes_count"],
            )
            result["training"] = {
                "id": str(training_run.id),
                "status": training_run.status,
                "model_version": training_run.resulting_model_version,
                "test_metrics": training_run.test_metrics,
                "mode": training_mode,
                "trigger_reason": decision["trigger_reason"],
            }
        except Exception:
            logger.exception("Full cycle: training step failed")
            result["training"] = {"skipped": False, "error": "training failed"}
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            return result

        if training_run.status != "completed" or not training_run.resulting_model_version:
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            return result

        # --- Step 5: Fairness check on new model ---
        try:
            fairness_reports = await self.fairness_checker.run_fairness_check(
                model_version=training_run.resulting_model_version,
                outcomes=[],  # evaluated from DB by the checker
                training_run_id=training_run.id,
            )
            if isinstance(fairness_reports, list):
                passed = all(r.passed for r in fairness_reports)
                result["fairness"] = {
                    "reports_count": len(fairness_reports),
                    "all_passed": passed,
                }
            else:
                result["fairness"] = {
                    "reports_count": 1,
                    "all_passed": getattr(fairness_reports, "passed", None),
                }
        except Exception:
            logger.exception("Full cycle: fairness check step failed")
            result["fairness"] = {"error": "fairness check failed"}

        # --- Step 6: Auto-promote if better ---
        try:
            promotion = await self.model_manager.auto_promote_if_better(
                training_run.id,
            )
            result["promotion"] = promotion
        except Exception:
            logger.exception("Full cycle: promotion step failed")
            result["promotion"] = {"error": "promotion failed"}

        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result

    # ------------------------------------------------------------------
    # Individual operations
    # ------------------------------------------------------------------

    async def run_evaluation_only(self) -> dict[str, Any]:
        """Run model evaluation only and return a summary."""
        timer = start_timer()
        try:
            eval_run = await self.evaluator.run_evaluation(
                evaluation_type="manual",
            )
            record_ml_evaluation(timer, ok=True)
            return {
                "id": str(eval_run.id),
                "model_version": eval_run.model_version,
                "dataset_size": eval_run.dataset_size,
                "metrics": eval_run.metrics,
                "retraining_triggered": eval_run.retraining_triggered,
                "drift_detected": eval_run.drift_detected,
                "started_at": eval_run.started_at.isoformat() if eval_run.started_at else None,
                "completed_at": eval_run.completed_at.isoformat() if eval_run.completed_at else None,
            }
        except Exception:
            record_ml_evaluation(timer, ok=False)
            logger.exception("run_evaluation_only failed")
            return {"error": "evaluation failed"}

    async def run_drift_check_only(self) -> dict[str, Any]:
        """Run drift detection only and return a summary."""
        try:
            snapshots = await self.drift_detector.check_all_drift()
            return {
                "snapshots_count": len(snapshots),
                "drift_detected": any(s.drift_detected for s in snapshots),
                "details": [
                    {
                        "id": str(s.id),
                        "snapshot_type": s.snapshot_type,
                        "feature_name": s.feature_name,
                        "drift_detected": s.drift_detected,
                        "p_value": s.p_value,
                    }
                    for s in snapshots
                ],
            }
        except Exception:
            logger.exception("run_drift_check_only failed")
            return {"error": "drift check failed"}

    async def backfill_outcomes(self) -> dict[str, Any]:
        """Backfill outcome records from historical data."""
        try:
            collector = OutcomeCollector(self.db)
            return await collector.backfill_outcomes()
        except Exception:
            logger.exception("backfill_outcomes failed")
            return {"error": "backfill failed"}

    async def _build_training_decision(
        self,
        eval_run: Any,
        any_drift: bool,
        triggered_by: str,
        preferred_mode: str | None = None,
    ) -> dict[str, Any]:
        latest_completed_training = await self._latest_completed_training()
        new_outcomes_count = await self._new_outcomes_since_training(
            latest_completed_training.started_at if latest_completed_training else None
        )

        age_hours_since_training: float | None = None
        if latest_completed_training and latest_completed_training.started_at:
            age_hours_since_training = (
                datetime.now(timezone.utc) - latest_completed_training.started_at
            ).total_seconds() / 3600

        retrain_reasons: list[str] = []
        if eval_run.retraining_triggered:
            retrain_reasons.append("evaluation_threshold")
        if any_drift:
            retrain_reasons.append("drift_detected")
        if new_outcomes_count >= settings.eval_retrain_min_new_outcomes:
            retrain_reasons.append("new_outcomes_threshold")
        if (
            age_hours_since_training is not None
            and age_hours_since_training >= settings.eval_retrain_max_hours_without_training
        ):
            retrain_reasons.append("max_training_age_exceeded")

        since_7d = datetime.now(timezone.utc) - timedelta(days=7)
        failed_runs_7d = int(
            (
                await self.db.execute(
                    select(func.count()).select_from(TrainingRun).where(
                        TrainingRun.started_at >= since_7d,
                        TrainingRun.status == "failed",
                    )
                )
            ).scalar()
            or 0
        )
        total_runs_7d = int(
            (
                await self.db.execute(
                    select(func.count()).select_from(TrainingRun).where(
                        TrainingRun.started_at >= since_7d
                    )
                )
            ).scalar()
            or 0
        )
        failure_rate_7d = (
            failed_runs_7d / total_runs_7d if total_runs_7d >= 1 else 0.0
        )
        degraded_mode_active = (
            total_runs_7d >= settings.training_degraded_mode_min_runs
            and failure_rate_7d >= settings.training_degraded_mode_failure_rate_threshold
        )
        if degraded_mode_active:
            retrain_reasons.append("degraded_mode_active")

        training_needed = bool(retrain_reasons)
        configured_cycle_mode = (preferred_mode or settings.training_default_cycle_mode).lower()
        if configured_cycle_mode not in {"fast", "full"}:
            configured_cycle_mode = "fast"
        training_mode = "fast" if any_drift or degraded_mode_active else configured_cycle_mode

        trigger_reason = "none"
        if retrain_reasons:
            # Keep the highest-signal reason first for easy operator scanning.
            priority = [
                "drift_detected",
                "evaluation_threshold",
                "new_outcomes_threshold",
                "max_training_age_exceeded",
            ]
            for reason in priority:
                if reason in retrain_reasons:
                    trigger_reason = reason
                    break

        return {
            "training_needed": training_needed,
            "training_mode": training_mode,
            "trigger_reason": trigger_reason,
            "reasons": retrain_reasons,
            "skip_reason": "policy_gates_not_triggered",
            "new_outcomes_count": new_outcomes_count,
            "age_hours_since_last_training": age_hours_since_training,
            "thresholds": {
                "min_new_outcomes": settings.eval_retrain_min_new_outcomes,
                "max_hours_without_training": settings.eval_retrain_max_hours_without_training,
                "degraded_mode_failure_rate_threshold": settings.training_degraded_mode_failure_rate_threshold,
                "degraded_mode_min_runs": settings.training_degraded_mode_min_runs,
            },
            "degraded_mode": {
                "active": degraded_mode_active,
                "failed_runs_7d": failed_runs_7d,
                "total_runs_7d": total_runs_7d,
                "failure_rate_7d": round(failure_rate_7d, 4),
            },
        }

    async def _latest_completed_training(self) -> TrainingRun | None:
        result = await self.db.execute(
            select(TrainingRun)
            .where(TrainingRun.status == "completed")
            .order_by(TrainingRun.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _new_outcomes_since_training(
        self,
        since: datetime | None,
    ) -> int:
        if since is None:
            result = await self.db.execute(select(func.count()).select_from(OutcomeRecord))
            return int(result.scalar() or 0)

        window_floor = max(
            since,
            datetime.now(timezone.utc) - timedelta(days=settings.training_recent_outcome_window_days),
        )
        result = await self.db.execute(
            select(func.count())
            .select_from(OutcomeRecord)
            .where(OutcomeRecord.outcome_recorded_at >= window_floor)
        )
        return int(result.scalar() or 0)
