from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
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
    "last_run_started_at": None,
    "last_run_completed_at": None,
    "last_run_result": None,
}


class AIEngineOrchestrator:
    """One orchestration backbone connecting ingest -> features/embeddings -> ML loop."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_full_graph(self, trigger: str = "manual") -> dict[str, Any]:
        started_at = datetime.now(timezone.utc).isoformat()
        _engine_runtime_state["status"] = "running"
        _engine_runtime_state["last_run_started_at"] = started_at

        result: dict[str, Any] = {
            "trigger": trigger,
            "started_at": started_at,
            "ingest": None,
            "feature_embedding": None,
            "ml": None,
            "completed_at": None,
        }

        result["ingest"] = await self.run_ingest_phase()
        result["feature_embedding"] = await self.run_feature_embedding_phase()
        result["ml"] = await self.run_ml_phase(trigger=f"engine:{trigger}")

        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        _engine_runtime_state["status"] = "idle"
        _engine_runtime_state["last_run_completed_at"] = result["completed_at"]
        _engine_runtime_state["last_run_result"] = result
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

            sem = asyncio.Semaphore(5)
            errors: list[dict[str, str]] = []
            processed = 0

            async def process_program(program_id: UUID) -> None:
                nonlocal processed
                async with sem:
                    try:
                        await extractor.extract_program_features(program_id)
                        await embedder.generate_program_embedding(program_id)
                        processed += 1
                    except Exception as exc:
                        errors.append({"program_id": str(program_id), "error": str(exc)})

            await asyncio.gather(*(process_program(pid) for pid in program_ids))
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
