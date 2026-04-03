"""Perpetual knowledge engine loop.

The heartbeat of the knowledge engine. Continuously:
1. Picks URLs from the frontier
2. Ingests content via appropriate adapter
3. Extracts knowledge via LLM
4. Discovers new sources
5. Respects throttle (RPM), steering directives, and bias controls

Controlled by admin via EngineDirective rows and API.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import get_engine_bootstrap_urls, settings
from unipaith.crawler.knowledge_extractor import KnowledgeExtractor
from unipaith.crawler.source_discoverer import SourceDiscoverer
from unipaith.crawler.universal_ingestor import IngestedContent, detect_adapter, get_adapter
from unipaith.models.knowledge import (
    CrawlFrontier,
    EngineDirective,
    EngineLoopSnapshot,
    KnowledgeDocument,
)

logger = logging.getLogger("unipaith.engine_loop")


class EngineLoopState:
    """Mutable runtime state for the engine loop, observable from admin."""

    def __init__(self) -> None:
        self.status: str = "idle"
        self.rpm: int = settings.engine_loop_default_rpm
        self.requests_this_minute: int = 0
        self.minute_started_at: float = time.monotonic()
        self.total_processed: int = 0
        self.total_errors: int = 0
        self.total_discovered: int = 0
        self.last_tick_at: str | None = None
        self.last_error: str | None = None
        self.paused: bool = False
        self.current_url: str | None = None
        self.session_started_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rpm": self.rpm,
            "requests_this_minute": self.requests_this_minute,
            "total_processed": self.total_processed,
            "total_errors": self.total_errors,
            "total_discovered": self.total_discovered,
            "last_tick_at": self.last_tick_at,
            "last_error": self.last_error,
            "paused": self.paused,
            "current_url": self.current_url,
            "session_started_at": self.session_started_at,
        }


_engine_state = EngineLoopState()


def get_engine_state() -> EngineLoopState:
    return _engine_state


_SNAPSHOT_SINGLETON_ID = 1


class EngineLoop:
    """The perpetual knowledge consumption loop."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.extractor = KnowledgeExtractor(db)
        self.discoverer = SourceDiscoverer(db)
        self.state = _engine_state

    async def _count_pending_frontier(self) -> int:
        now = datetime.now(UTC)
        ready = (CrawlFrontier.next_crawl_after.is_(None)) | (
            CrawlFrontier.next_crawl_after <= now
        )
        result = await self.db.execute(
            select(func.count())
            .select_from(CrawlFrontier)
            .where(
                CrawlFrontier.status == "pending",
                ready,
            )
        )
        return int(result.scalar() or 0)

    async def _persist_tick_snapshot(
        self,
        *,
        result: dict[str, Any],
        pending_before: int,
        pending_after: int,
        bootstrap_added: int,
        batch_was_empty: bool,
        tick_status: str,
    ) -> None:
        row = await self.db.get(EngineLoopSnapshot, _SNAPSHOT_SINGLETON_ID)
        if row is None:
            row = EngineLoopSnapshot(id=_SNAPSHOT_SINGLETON_ID)
            self.db.add(row)

        now = datetime.now(UTC)
        row.last_tick_at = now
        row.last_processed = int(result.get("processed", 0))
        row.last_errors = int(result.get("errors", 0))
        row.last_discovered = int(result.get("discovered", 0))
        row.last_skipped = int(result.get("skipped", 0))
        row.last_bootstrap_added = bootstrap_added
        row.frontier_pending_before = pending_before
        row.frontier_pending_after = pending_after
        row.batch_was_empty = batch_was_empty
        row.tick_status = tick_status
        row.last_error_message = (self.state.last_error or "")[:2000] or None
        row.cumulative_processed = self.state.total_processed
        row.cumulative_errors = self.state.total_errors
        row.ai_mock_mode = bool(settings.ai_mock_mode or settings.gpu_mode == "mock")
        row.gpu_mode = settings.gpu_mode

        await self.db.flush()

    async def run_tick(self) -> dict[str, Any]:
        """Run one tick of the engine loop.

        A tick processes one batch of frontier URLs, then optionally runs discovery.
        Called by the scheduler at regular intervals.
        """
        if self.state.paused:
            await self._persist_tick_snapshot(
                result={"processed": 0, "errors": 0, "discovered": 0, "skipped": 0},
                pending_before=0,
                pending_after=0,
                bootstrap_added=0,
                batch_was_empty=True,
                tick_status="paused",
            )
            return {"status": "paused"}

        self.state.status = "running"
        self.state.last_tick_at = datetime.now(UTC).isoformat()
        if not self.state.session_started_at:
            self.state.session_started_at = self.state.last_tick_at

        result: dict[str, Any] = {
            "processed": 0,
            "errors": 0,
            "discovered": 0,
            "skipped": 0,
        }
        bootstrap_added = 0
        pending_before = await self._count_pending_frontier()
        batch_was_empty = True
        tick_status = "ok"

        try:
            directives = await self._load_directives()
            self._apply_directives(directives)

            if settings.engine_bootstrap_enabled and pending_before == 0:
                bootstrap_added = await self.discoverer.ensure_bootstrap_frontier(
                    get_engine_bootstrap_urls(),
                )

            batch = await self.discoverer.get_next_batch(
                batch_size=min(self.state.rpm, 10),
            )

            if not batch:
                discovery_result = await self.discoverer.run_discovery_cycle(max_new_urls=20)
                result["discovered"] = sum(discovery_result.values())
                self.state.total_discovered += result["discovered"]
                pending_after = await self._count_pending_frontier()
                logger.info(
                    "Knowledge engine tick: no batch; discovery=%s "
                    "pending_before=%s pending_after=%s bootstrap_added=%s "
                    "ai_mock=%s gpu_mode=%s pid=%s",
                    discovery_result,
                    pending_before,
                    pending_after,
                    bootstrap_added,
                    settings.ai_mock_mode,
                    settings.gpu_mode,
                    os.getpid(),
                )
                await self._persist_tick_snapshot(
                    result=result,
                    pending_before=pending_before,
                    pending_after=pending_after,
                    bootstrap_added=bootstrap_added,
                    batch_was_empty=True,
                    tick_status="idle_no_batch",
                )
                self.state.status = "idle"
                return result

            batch_was_empty = False

            for frontier_item in batch:
                if self.state.paused:
                    break

                if not self._check_rpm():
                    result["skipped"] += 1
                    continue

                try:
                    self.state.current_url = frontier_item.url
                    docs = await self._process_frontier_item(frontier_item)
                    result["processed"] += len(docs)
                    self.state.total_processed += len(docs)
                    await self.discoverer.mark_crawled(frontier_item.id, success=True)
                except Exception as e:
                    logger.warning("Failed to process %s: %s", frontier_item.url, e)
                    result["errors"] += 1
                    self.state.total_errors += 1
                    self.state.last_error = str(e)[:500]
                    await self.discoverer.mark_crawled(
                        frontier_item.id,
                        success=False,
                        error=str(e)[:500],
                    )

                self.state.requests_this_minute += 1
                await asyncio.sleep(max(0.5, 60.0 / max(self.state.rpm, 1)))

            if result["processed"] > 0 and self.state.total_processed % 20 == 0:
                discovery_result = await self.discoverer.run_discovery_cycle(max_new_urls=10)
                result["discovered"] = sum(discovery_result.values())
                self.state.total_discovered += result["discovered"]

            pending_after = await self._count_pending_frontier()
            logger.info(
                "Knowledge engine tick: processed=%s errors=%s discovered=%s skipped=%s "
                "pending_after=%s bootstrap_added=%s ai_mock=%s gpu_mode=%s pid=%s",
                result.get("processed"),
                result.get("errors"),
                result.get("discovered"),
                result.get("skipped"),
                pending_after,
                bootstrap_added,
                settings.ai_mock_mode,
                settings.gpu_mode,
                os.getpid(),
            )
            await self._persist_tick_snapshot(
                result=result,
                pending_before=pending_before,
                pending_after=pending_after,
                bootstrap_added=bootstrap_added,
                batch_was_empty=False,
                tick_status="ok",
            )

        except Exception as e:
            logger.exception("Engine loop tick failed")
            self.state.last_error = str(e)[:500]
            result["errors"] += 1
            tick_status = "error"
            pending_after = await self._count_pending_frontier()
            await self._persist_tick_snapshot(
                result=result,
                pending_before=pending_before,
                pending_after=pending_after,
                bootstrap_added=bootstrap_added,
                batch_was_empty=batch_was_empty,
                tick_status=tick_status,
            )
        finally:
            self.state.current_url = None
            self.state.status = "idle"

        await self.db.flush()
        return result

    async def _process_frontier_item(
        self,
        item: CrawlFrontier,
    ) -> list[KnowledgeDocument]:
        """Ingest a single frontier URL and extract knowledge."""
        adapter_type = item.content_format_hint or detect_adapter(item.url)
        adapter = get_adapter(adapter_type)

        ingested_items: list[IngestedContent] = await adapter.ingest(item.url)
        documents: list[KnowledgeDocument] = []

        for content in ingested_items:
            doc = await self.extractor.process_raw_content(
                raw_text=content.raw_text,
                source_url=content.source_url,
                content_format=content.content_format,
                frontier_id=item.id,
                metadata=content.metadata,
            )
            if doc:
                documents.append(doc)

        return documents

    def _check_rpm(self) -> bool:
        """Check if we're within the RPM throttle."""
        now = time.monotonic()
        if now - self.state.minute_started_at >= 60:
            self.state.requests_this_minute = 0
            self.state.minute_started_at = now
        return self.state.requests_this_minute < self.state.rpm

    async def _load_directives(self) -> list[EngineDirective]:
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(EngineDirective).where(
                EngineDirective.is_active.is_(True),
                (EngineDirective.expires_at.is_(None)) | (EngineDirective.expires_at > now),
            )
        )
        return list(result.scalars().all())

    def _apply_directives(self, directives: list[EngineDirective]) -> None:
        """Apply admin directives to engine state."""
        for d in directives:
            if d.directive_type == "throttle":
                rpm = d.directive_value.get("rpm")
                if rpm and isinstance(rpm, (int, float)):
                    self.state.rpm = max(1, min(100, int(rpm)))

            elif d.directive_type == "pause":
                self.state.paused = True

            elif d.directive_type == "resume":
                self.state.paused = False

    async def get_stats(self) -> dict[str, Any]:
        """Get engine loop statistics for admin dashboard."""
        total_docs = await self.db.scalar(select(func.count()).select_from(KnowledgeDocument))
        active_docs = await self.db.scalar(
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(
                KnowledgeDocument.is_active.is_(True),
                KnowledgeDocument.processing_status == "completed",
            )
        )
        pending_frontier = await self.db.scalar(
            select(func.count())
            .select_from(CrawlFrontier)
            .where(
                CrawlFrontier.status == "pending",
            )
        )
        failed_frontier = await self.db.scalar(
            select(func.count())
            .select_from(CrawlFrontier)
            .where(
                CrawlFrontier.status == "failed",
            )
        )

        format_counts_result = await self.db.execute(
            select(
                KnowledgeDocument.content_format,
                func.count(),
            )
            .where(KnowledgeDocument.processing_status == "completed")
            .group_by(KnowledgeDocument.content_format)
        )
        format_counts = {row[0]: row[1] for row in format_counts_result.all()}

        type_counts_result = await self.db.execute(
            select(
                KnowledgeDocument.content_type,
                func.count(),
            )
            .where(KnowledgeDocument.processing_status == "completed")
            .group_by(KnowledgeDocument.content_type)
        )
        type_counts = {row[0]: row[1] for row in type_counts_result.all()}

        snap_row = await self.db.get(EngineLoopSnapshot, _SNAPSHOT_SINGLETON_ID)
        persisted: dict[str, Any] | None = None
        if snap_row is not None:
            persisted = {
                "last_tick_at": snap_row.last_tick_at.isoformat()
                if snap_row.last_tick_at
                else None,
                "last_processed": snap_row.last_processed,
                "last_errors": snap_row.last_errors,
                "last_discovered": snap_row.last_discovered,
                "last_skipped": snap_row.last_skipped,
                "last_bootstrap_added": snap_row.last_bootstrap_added,
                "frontier_pending_before": snap_row.frontier_pending_before,
                "frontier_pending_after": snap_row.frontier_pending_after,
                "batch_was_empty": snap_row.batch_was_empty,
                "tick_status": snap_row.tick_status,
                "last_error_message": snap_row.last_error_message,
                "cumulative_processed": snap_row.cumulative_processed,
                "cumulative_errors": snap_row.cumulative_errors,
                "ai_mock_mode": snap_row.ai_mock_mode,
                "gpu_mode": snap_row.gpu_mode,
            }

        runtime_engine = self.state.to_dict()
        if persisted and persisted.get("last_tick_at"):
            runtime_engine["last_tick_at"] = persisted["last_tick_at"]

        return {
            "engine": runtime_engine,
            "engine_persisted": persisted,
            "engine_runtime_flags": {
                "openai_key_configured": bool(settings.openai_api_key),
                "ai_mock_mode": settings.ai_mock_mode,
                "gpu_mode": settings.gpu_mode,
                "engine_bootstrap_enabled": settings.engine_bootstrap_enabled,
            },
            "knowledge": {
                "total_documents": total_docs or 0,
                "active_documents": active_docs or 0,
                "by_format": format_counts,
                "by_type": type_counts,
            },
            "frontier": {
                "pending": pending_frontier or 0,
                "failed": failed_frontier or 0,
            },
        }
