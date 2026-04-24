"""Orchestrator — top-level pipeline coordinator for the data crawler."""

from __future__ import annotations

import logging
from datetime import UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.crawler.deduplicator import Deduplicator
from unipaith.crawler.engine import CrawlerEngine
from unipaith.crawler.extractor import LLMExtractor
from unipaith.crawler.ingestor import AutoIngestor
from unipaith.crawler.source_registry import SourceRegistry
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.matching import DataSource

logger = logging.getLogger(__name__)


class CrawlerOrchestrator:
    """Coordinates the full crawl-extract-deduplicate-ingest pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_scheduled_crawls(self) -> dict:
        """Find all due sources and run the full pipeline for each."""
        registry = SourceRegistry(self.db)
        due_sources = await registry.get_due_sources()

        results: list[dict] = []
        for source in due_sources:
            try:
                result = await self.run_full_pipeline(source.id)
                # Commit after each successful pipeline so data is persisted
                await self.db.commit()
                results.append(result)
            except Exception as exc:
                logger.error("Pipeline failed for source %s: %s", source.id, exc)
                # Rollback only the failed source's changes
                await self.db.rollback()
                results.append(
                    {
                        "source_id": str(source.id),
                        "source_name": source.source_name,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        logger.info(
            "Scheduled crawls complete: %d sources processed",
            len(results),
        )
        return {
            "sources_processed": len(results),
            "results": results,
        }

    async def run_full_pipeline(self, source_id: UUID) -> dict:
        """Execute the full pipeline: crawl -> extract -> deduplicate -> ingest.

        Also triggers the AI pipeline for any ingested programs.
        """
        registry = SourceRegistry(self.db)
        source = await registry.get_source(source_id)

        logger.info("Starting full pipeline for source '%s' (%s)", source.source_name, source_id)

        # Step 1: Crawl
        engine = CrawlerEngine(self.db)
        job = await engine.start_crawl(source_id)

        if job.status == "failed":
            await registry.update_source_health(source_id, success=False)
            return {
                "source_id": str(source_id),
                "source_name": source.source_name,
                "job_id": str(job.id),
                "status": "crawl_failed",
                "pages_crawled": job.pages_crawled,
                "error_log": job.error_log,
            }

        # Step 2: Extract
        extractor = LLMExtractor(self.db)
        extracted_count = await extractor.process_unprocessed(job.id)

        # Step 3: Deduplicate
        deduplicator = Deduplicator(self.db)
        dedup_counts = await deduplicator.deduplicate_batch(job.id)

        # Step 4: Ingest
        ingestor = AutoIngestor(self.db)
        ingest_counts = await ingestor.process_crawl_job(job.id)

        # Step 5: Update source health
        await registry.update_source_health(
            source_id,
            success=True,
            pages_crawled=job.pages_crawled,
        )

        # Step 6: Trigger AI pipeline for newly ingested programs
        await self._trigger_ai_pipeline(job.id)

        result = {
            "source_id": str(source_id),
            "source_name": source.source_name,
            "job_id": str(job.id),
            "status": "completed",
            "pages_crawled": job.pages_crawled,
            "pages_failed": job.pages_failed,
            "items_extracted": extracted_count,
            "deduplication": dedup_counts,
            "ingestion": ingest_counts,
        }

        logger.info("Pipeline complete for source '%s': %s", source.source_name, result)
        return result

    async def _trigger_ai_pipeline(self, crawl_job_id: UUID) -> None:
        """Call Phase 2's embedding/feature pipeline for newly ingested programs.

        Looks for auto_ingested programs and triggers feature extraction +
        embedding generation for each new or updated program.
        """
        stmt = select(ExtractedProgram).where(
            ExtractedProgram.crawl_job_id == crawl_job_id,
            ExtractedProgram.review_status == "auto_ingested",
            ExtractedProgram.matched_program_id.isnot(None),
        )
        result = await self.db.execute(stmt)
        eps = list(result.scalars().all())

        if not eps:
            return

        program_ids = [ep.matched_program_id for ep in eps if ep.matched_program_id]
        logger.info(
            "Triggering AI pipeline for %d programs from job %s",
            len(program_ids),
            crawl_job_id,
        )

        # AI engine removed — skip feature extraction and embedding
        for program_id in program_ids:
            logger.debug("Skipping AI pipeline for %s", program_id)

    async def crawl_single_url(
        self,
        url: str,
        source_id: UUID | None = None,
    ) -> dict:
        """One-off crawl of a single URL for testing.

        If source_id is not provided, uses or creates a generic test source.
        """
        import hashlib
        from datetime import datetime

        import aiohttp

        from unipaith.config import settings
        from unipaith.models.matching import RawIngestedData

        # Resolve source
        if source_id:
            source = await self.db.get(DataSource, source_id)
            if not source:
                raise NotFoundException(f"Data source {source_id} not found")
        else:
            # Find or create a test source
            stmt = select(DataSource).where(DataSource.source_name == "Manual Test Crawl")
            result = await self.db.execute(stmt)
            source = result.scalar_one_or_none()
            if not source:
                source = DataSource(
                    source_name="Manual Test Crawl",
                    source_url=url,
                    source_type="manual",
                    data_category="test",
                    is_active=True,
                )
                self.db.add(source)
                await self.db.flush()

        # Create job
        job = CrawlJob(
            source_id=source.id,
            status="running",
            started_at=datetime.now(UTC),
        )
        self.db.add(job)
        await self.db.flush()

        # Fetch URL
        try:
            timeout = aiohttp.ClientTimeout(total=settings.crawler_request_timeout)
            headers = {"User-Agent": settings.crawler_user_agent}
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        job.status = "failed"
                        job.error_log = [{"url": url, "status": resp.status}]
                        job.completed_at = datetime.now(UTC)
                        await self.db.flush()
                        return {
                            "job_id": str(job.id),
                            "status": "failed",
                            "error": f"HTTP {resp.status}",
                        }
                    html = await resp.text()
        except Exception as exc:
            job.status = "failed"
            job.error_log = [{"url": url, "error": str(exc)}]
            job.completed_at = datetime.now(UTC)
            await self.db.flush()
            return {
                "job_id": str(job.id),
                "status": "failed",
                "error": str(exc),
            }

        # Store raw
        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        raw = RawIngestedData(
            source_id=source.id,
            raw_content=html,
            content_hash=content_hash,
            processed=False,
        )
        self.db.add(raw)
        job.pages_crawled = 1

        # Extract
        extractor = LLMExtractor(self.db)
        await self.db.flush()
        extracted = await extractor.extract_from_raw(raw.id, job.id)

        # Deduplicate
        deduplicator = Deduplicator(self.db)
        for ep in extracted:
            await deduplicator.match_and_classify(ep.id)

        job.status = "completed"
        job.completed_at = datetime.now(UTC)
        await self.db.flush()

        return {
            "job_id": str(job.id),
            "source_id": str(source.id),
            "status": "completed",
            "url": url,
            "pages_crawled": 1,
            "items_extracted": len(extracted),
            "extracted_programs": [
                {
                    "id": str(ep.id),
                    "program_name": ep.program_name,
                    "institution_name": ep.institution_name,
                    "match_type": ep.match_type,
                    "confidence": float(ep.extraction_confidence or 0),
                }
                for ep in extracted
            ],
        }
