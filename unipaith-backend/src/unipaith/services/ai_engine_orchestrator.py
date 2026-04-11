from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.embedding_pipeline import EmbeddingPipeline
from unipaith.ai.feature_extraction import FeatureExtractor
from unipaith.crawler.orchestrator import CrawlerOrchestrator
from unipaith.ml.orchestrator import MLOrchestrator
from unipaith.models.institution import Program

logger = logging.getLogger("unipaith.ai_engine_orchestrator")


_engine_runtime_state: dict[str, Any] = {
    "status": "idle",
    "current_stage": None,
    "stage_started_at": None,
    "stage_completed_at": None,
    "last_stage_durations_ms": {},
    "last_stage_statuses": {},
    "last_error": None,
    "last_run_started_at": None,
    "last_run_completed_at": None,
    "last_run_result": None,
}


class AIEngineOrchestrator:
    """One orchestration backbone connecting ingest -> features/embeddings -> ML loop."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _begin_stage(self, stage: str) -> tuple[str, float]:
        started_at = datetime.now(UTC).isoformat()
        _engine_runtime_state["current_stage"] = stage
        _engine_runtime_state["stage_started_at"] = started_at
        return started_at, time.monotonic()

    def _complete_stage(self, stage: str, started_monotonic: float, status: str) -> None:
        completed_at = datetime.now(UTC).isoformat()
        duration_ms = round((time.monotonic() - started_monotonic) * 1000, 2)
        _engine_runtime_state["stage_completed_at"] = completed_at
        _engine_runtime_state["last_stage_durations_ms"] = {
            **(_engine_runtime_state.get("last_stage_durations_ms") or {}),
            stage: duration_ms,
        }
        _engine_runtime_state["last_stage_statuses"] = {
            **(_engine_runtime_state.get("last_stage_statuses") or {}),
            stage: status,
        }

    async def run_full_graph(self, trigger: str = "manual") -> dict[str, Any]:
        started_at = datetime.now(UTC).isoformat()
        _engine_runtime_state["status"] = "running"
        _engine_runtime_state["current_stage"] = "ingest"
        _engine_runtime_state["last_error"] = None
        _engine_runtime_state["last_run_started_at"] = started_at

        result: dict[str, Any] = {
            "trigger": trigger,
            "started_at": started_at,
            "ingest": None,
            "feature_embedding": None,
            "ml": None,
            "completed_at": None,
        }

        _, ingest_t0 = self._begin_stage("ingest")
        result["ingest"] = await self.run_ingest_phase()
        self._complete_stage(
            "ingest",
            ingest_t0,
            "ok" if result["ingest"].get("status") == "ok" else "error",
        )

        _, feat_t0 = self._begin_stage("feature_embedding")
        result["feature_embedding"] = await self.run_feature_embedding_phase()
        self._complete_stage(
            "feature_embedding",
            feat_t0,
            "ok" if result["feature_embedding"].get("status") == "ok" else "error",
        )

        _, ml_t0 = self._begin_stage("ml")
        result["ml"] = await self.run_ml_phase(trigger=f"engine:{trigger}")
        self._complete_stage(
            "ml",
            ml_t0,
            "ok" if result["ml"].get("status") == "ok" else "error",
        )

        result["completed_at"] = datetime.now(UTC).isoformat()
        _engine_runtime_state["status"] = "idle"
        _engine_runtime_state["current_stage"] = None
        _engine_runtime_state["last_run_completed_at"] = result["completed_at"]
        _engine_runtime_state["last_run_result"] = result
        _engine_runtime_state["stage_started_at"] = None
        _engine_runtime_state["stage_completed_at"] = result["completed_at"]

        if result["ingest"].get("status") == "error":
            _engine_runtime_state["last_error"] = result["ingest"].get("error")
        elif result["feature_embedding"].get("status") == "error":
            _engine_runtime_state["last_error"] = result["feature_embedding"].get("error")
        elif result["ml"].get("status") == "error":
            _engine_runtime_state["last_error"] = result["ml"].get("error")

        return result

    async def run_ingest_phase(self) -> dict[str, Any]:
        try:
            orchestrator = CrawlerOrchestrator(self.db)
            crawl_result = await orchestrator.run_scheduled_crawls()
            await self.db.commit()
            return {"status": "ok", "result": crawl_result}
        except Exception as exc:
            logger.exception("Ingest phase failed")
            await self.db.rollback()
            return {"status": "error", "error": str(exc)}

    async def run_feature_embedding_phase(self) -> dict[str, Any]:
        try:
            result = await self.db.execute(select(Program.id).where(Program.is_published.is_(True)))
            program_ids: list[UUID] = [row[0] for row in result.all()]
            if not program_ids:
                return {"status": "ok", "programs_processed": 0}

            extractor = FeatureExtractor(self.db)
            embedder = EmbeddingPipeline(self.db)

            errors: list[dict[str, str]] = []
            processed = 0

            for pid in program_ids:
                try:
                    await extractor.extract_program_features(pid)
                    await embedder.generate_program_embedding(pid)
                    processed += 1
                except Exception as exc:
                    errors.append({"program_id": str(pid), "error": str(exc)})
            await self.db.commit()
            return {
                "status": "ok",
                "programs_targeted": len(program_ids),
                "programs_processed": processed,
                "errors": errors,
            }
        except Exception as exc:
            logger.exception("Feature/embedding phase failed")
            await self.db.rollback()
            return {"status": "error", "error": str(exc)}

    async def run_ml_phase(self, trigger: str) -> dict[str, Any]:
        try:
            ml = MLOrchestrator(self.db)
            cycle = await ml.run_full_cycle(triggered_by=trigger)
            await self.db.commit()
            return {"status": "ok", "result": cycle}
        except Exception as exc:
            logger.exception("ML phase failed")
            await self.db.rollback()
            return {"status": "error", "error": str(exc)}

    def get_runtime_state(self) -> dict[str, Any]:
        return dict(_engine_runtime_state)
