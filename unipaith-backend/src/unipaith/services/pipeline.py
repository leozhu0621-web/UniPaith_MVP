"""Continuous three-stage pipeline.

Stage 1 (crawl) and Stage 3 (ML) run 24/7 on Fargate as asyncio tasks.
Stage 2 (extract) auto-switches between a local Ollama worker (when online)
and an OpenAI fallback on Fargate (when the local worker's heartbeat is stale).

The pipeline never idles unless the admin flips the master switch off.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import get_engine_bootstrap_urls, settings
from unipaith.database import async_session
from unipaith.models.knowledge import CrawlFrontier, KnowledgeDocument
from unipaith.models.pipeline import PipelineStageSnapshot

logger = logging.getLogger("unipaith.pipeline")

STAGES = ("crawl", "extract", "ml")


class BudgetGate:
    """Blocks callers when hourly OpenAI spend exceeds the budget."""

    def __init__(self, budget_per_hour: float = 5.0):
        self.budget_per_hour = budget_per_hour
        self.spent_this_hour = 0.0
        self._hour_start = time.monotonic()

    async def acquire(self, estimated_cost: float) -> None:
        while self.spent_this_hour + estimated_cost > self.budget_per_hour:
            await asyncio.sleep(5)
            self._maybe_reset()
        self.spent_this_hour += estimated_cost

    def _maybe_reset(self) -> None:
        if time.monotonic() - self._hour_start >= 3600:
            self.spent_this_hour = 0.0
            self._hour_start = time.monotonic()


class ContinuousPipeline:
    """Three-stage pipeline. Runs 24/7. Never idles unless switched off."""

    def __init__(self) -> None:
        self.enabled = settings.pipeline_enabled
        self.budget_gate = BudgetGate(settings.pipeline_extract_budget_per_hour)
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        logger.info("Pipeline starting (enabled=%s)", self.enabled)
        self._tasks = [
            asyncio.create_task(self._crawl_loop(), name="pipeline-crawl"),
            asyncio.create_task(self._extract_fallback_loop(), name="pipeline-extract-fallback"),
            asyncio.create_task(self._ml_loop(), name="pipeline-ml"),
            asyncio.create_task(self._budget_reset_loop(), name="pipeline-budget"),
        ]

    async def stop(self) -> None:
        logger.info("Pipeline stopping")
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    # ------------------------------------------------------------------
    # Stage 1: Continuous Crawl
    # ------------------------------------------------------------------

    async def _crawl_loop(self) -> None:
        logger.info("Stage 1 (crawl) started")
        while True:
            try:
                if not self.enabled:
                    await self._update_stage("crawl", "paused")
                    await asyncio.sleep(10)
                    continue

                await self._update_stage("crawl", "running")
                async with async_session() as db:
                    await self._crawl_one(db)
                    await db.commit()

                delay = 60.0 / max(settings.pipeline_crawl_rpm, 1)
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Crawl loop error")
                await self._update_stage("crawl", "error", error=True)
                await asyncio.sleep(10)

    async def _crawl_one(self, db: AsyncSession) -> int:
        from unipaith.crawler.knowledge_extractor import KnowledgeExtractor
        from unipaith.crawler.source_discoverer import SourceDiscoverer
        from unipaith.crawler.universal_ingestor import detect_adapter, get_adapter

        discoverer = SourceDiscoverer(db)
        extractor = KnowledgeExtractor(db)

        now = datetime.now(UTC)
        ready = (CrawlFrontier.next_crawl_after.is_(None)) | (
            CrawlFrontier.next_crawl_after <= now
        )
        result = await db.execute(
            select(CrawlFrontier)
            .where(CrawlFrontier.status == "pending", ready)
            .order_by(CrawlFrontier.priority.desc(), CrawlFrontier.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        item = result.scalar_one_or_none()

        if item is None:
            if settings.engine_bootstrap_enabled:
                pending_count = await db.scalar(
                    select(func.count()).select_from(CrawlFrontier)
                    .where(CrawlFrontier.status == "pending")
                )
                if (pending_count or 0) == 0:
                    added = await discoverer.ensure_bootstrap_frontier(
                        get_engine_bootstrap_urls()
                    )
                    if added:
                        logger.info("Bootstrap: added %d seed URLs", added)

            discovery = await discoverer.run_discovery_cycle(max_new_urls=20)
            discovered = sum(discovery.values())
            await self._update_stage("crawl", "waiting", extra={
                "action": "discovery", "discovered": discovered,
            })
            return 0

        try:
            adapter_type = item.content_format_hint or detect_adapter(item.url)
            adapter = get_adapter(adapter_type)
            ingested_items = await adapter.ingest(item.url)

            stored = 0
            for content in ingested_items:
                doc = await extractor.store_raw(
                    raw_text=content.raw_text,
                    source_url=content.source_url,
                    content_format=content.content_format,
                    frontier_id=item.id,
                    metadata=content.metadata,
                )
                if doc:
                    stored += 1

            await discoverer.mark_crawled(item.id, success=True)
            await self._update_stage("crawl", "running", items=stored)
            return stored

        except Exception as exc:
            logger.warning("Failed to crawl %s: %s", item.url, exc)
            await discoverer.mark_crawled(item.id, success=False, error=str(exc)[:500])
            await self._update_stage("crawl", "running", error=True,
                                     last_error=str(exc)[:500])
            return 0

    # ------------------------------------------------------------------
    # Stage 2 Fallback: OpenAI on Fargate (auto-engages when local offline)
    # ------------------------------------------------------------------

    async def _extract_fallback_loop(self) -> None:
        logger.info("Stage 2 fallback (OpenAI) started — monitoring local worker heartbeat")
        while True:
            try:
                if not self.enabled:
                    await self._update_stage("extract", "paused")
                    await asyncio.sleep(10)
                    continue

                if await self._is_local_worker_alive():
                    await self._update_stage("extract", "local_online")
                    await asyncio.sleep(30)
                    continue

                await self._update_stage("extract", "fallback_running")
                async with async_session() as db:
                    doc = await self._pull_raw_doc(db)
                    if doc is None:
                        await self._update_stage("extract", "fallback_waiting")
                        await asyncio.sleep(settings.pipeline_extract_idle_seconds)
                        await db.rollback()
                        continue

                    await self.budget_gate.acquire(settings.pipeline_extract_cost_per_doc)

                    from unipaith.crawler.knowledge_extractor import KnowledgeExtractor
                    extractor = KnowledgeExtractor(db)
                    await extractor.extract_knowledge(doc)
                    await db.commit()
                    await self._update_stage("extract", "fallback_running", items=1)

            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Extract fallback loop error")
                await self._update_stage("extract", "error", error=True)
                await asyncio.sleep(10)

    async def _is_local_worker_alive(self) -> bool:
        timeout = settings.pipeline_extract_heartbeat_timeout_seconds
        cutoff = datetime.now(UTC) - timedelta(seconds=timeout)
        async with async_session() as db:
            snap = await db.get(PipelineStageSnapshot, "extract")
            if snap is None or snap.worker_heartbeat_at is None:
                return False
            return snap.worker_heartbeat_at > cutoff

    async def _pull_raw_doc(self, db: AsyncSession) -> KnowledgeDocument | None:
        result = await db.execute(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.processing_status == "raw")
            .order_by(KnowledgeDocument.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Stage 3: Continuous ML
    # ------------------------------------------------------------------

    async def _ml_loop(self) -> None:
        logger.info("Stage 3 (ML) started")
        while True:
            try:
                if not self.enabled:
                    await self._update_stage("ml", "paused")
                    await asyncio.sleep(10)
                    continue

                async with async_session() as db:
                    from unipaith.models.ml_loop import OutcomeRecord
                    count = await db.scalar(
                        select(func.count()).select_from(OutcomeRecord)
                    ) or 0

                threshold = settings.pipeline_ml_threshold
                if count < threshold:
                    await self._update_stage("ml", "waiting", extra={
                        "current_outcomes": count,
                        "required_outcomes": threshold,
                        "reason": "insufficient_outcomes",
                    })
                    await asyncio.sleep(settings.pipeline_ml_check_seconds)
                    continue

                await self._update_stage("ml", "training", extra={
                    "current_outcomes": count,
                    "required_outcomes": threshold,
                })
                async with async_session() as db:
                    from unipaith.ml.orchestrator import MLOrchestrator
                    orch = MLOrchestrator(db)
                    try:
                        result = await orch.run_full_cycle(
                            triggered_by="pipeline_continuous",
                            preferred_mode=settings.training_default_cycle_mode,
                        )
                        await db.commit()
                        await self._update_stage("ml", "completed", items=1, extra={
                            "current_outcomes": count,
                            "required_outcomes": threshold,
                            "cycle_result": {
                                k: v for k, v in result.items()
                                if k in ("evaluation", "training", "promotion", "decision")
                            },
                        })
                    except Exception as exc:
                        logger.exception("ML cycle failed")
                        await self._update_stage("ml", "error",
                                                 last_error=str(exc)[:500])

                await asyncio.sleep(settings.pipeline_ml_cooldown_seconds)

            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("ML loop error")
                await self._update_stage("ml", "error", error=True)
                await asyncio.sleep(30)

    # ------------------------------------------------------------------
    # Budget reset
    # ------------------------------------------------------------------

    async def _budget_reset_loop(self) -> None:
        while True:
            await asyncio.sleep(3600)
            self.budget_gate.spent_this_hour = 0.0
            self.budget_gate._hour_start = time.monotonic()
            logger.info("Budget counter reset")

    # ------------------------------------------------------------------
    # Stage snapshot persistence
    # ------------------------------------------------------------------

    async def _update_stage(
        self,
        stage: str,
        status: str,
        *,
        items: int = 0,
        error: bool = False,
        last_error: str | None = None,
        extra: dict | None = None,
    ) -> None:
        try:
            async with async_session() as db:
                snap = await db.get(PipelineStageSnapshot, stage)
                if snap is None:
                    snap = PipelineStageSnapshot(stage=stage)
                    db.add(snap)

                snap.status = status
                # Count as "activity" for last_activity_at: throughput, crawl/extract
                # runners, ML checks/training (waiting/training are not "running").
                counts_for_activity = (
                    items > 0
                    or status == "running"
                    or status.startswith("fallback")
                    or status
                    in (
                        "training",
                        "waiting",
                        "completed",
                        "local_online",
                        "error",
                    )
                )
                if counts_for_activity:
                    snap.last_activity_at = datetime.now(UTC)

                if items > 0 or status == "running" or status.startswith("fallback"):
                    snap.items_processed_total = (snap.items_processed_total or 0) + items

                    now = datetime.now(UTC)
                    if snap.hour_window_start is None or (
                        now - snap.hour_window_start > timedelta(hours=1)
                    ):
                        snap.hour_window_start = now
                        snap.items_processed_hour = items
                    else:
                        snap.items_processed_hour = (snap.items_processed_hour or 0) + items

                if error and last_error:
                    snap.last_error = last_error

                if extra:
                    snap.extra_json = {**(snap.extra_json or {}), **extra}

                if stage == "extract":
                    snap.budget_spent_this_hour = self.budget_gate.spent_this_hour
                    snap.budget_per_hour = self.budget_gate.budget_per_hour

                raw_count = await db.scalar(
                    select(func.count()).select_from(KnowledgeDocument)
                    .where(KnowledgeDocument.processing_status == "raw")
                )
                if stage == "extract":
                    snap.queue_depth = raw_count or 0
                elif stage == "crawl":
                    frontier_count = await db.scalar(
                        select(func.count()).select_from(CrawlFrontier)
                        .where(CrawlFrontier.status == "pending")
                    )
                    snap.queue_depth = frontier_count or 0

                await db.commit()
        except Exception:
            logger.debug("Failed to update stage snapshot for %s", stage, exc_info=True)


_pipeline: ContinuousPipeline | None = None


def get_pipeline() -> ContinuousPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ContinuousPipeline()
    return _pipeline
