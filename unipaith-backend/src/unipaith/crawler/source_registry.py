"""Source registry — CRUD and health tracking for DataSource entities."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import ConflictException, NotFoundException
from unipaith.models.crawler import CrawlSchedule, SourceURLPattern
from unipaith.models.matching import DataSource

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Manages data sources, their URL patterns, and crawl schedules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_source(
        self,
        name: str,
        url: str,
        source_type: str,
        category: str,
        frequency_hours: int,
        url_patterns: list[dict] | None = None,
    ) -> DataSource:
        """Register a new data source with optional URL patterns and schedule."""
        # Check duplicate name
        existing = await self.db.execute(select(DataSource).where(DataSource.source_name == name))
        if existing.scalar_one_or_none():
            raise ConflictException(f"Data source with name '{name}' already exists")

        source = DataSource(
            source_name=name,
            source_url=url,
            source_type=source_type,
            data_category=category,
            crawl_frequency=str(frequency_hours),
            reliability_score=Decimal("0.50"),
            is_active=True,
        )
        self.db.add(source)
        await self.db.flush()

        # Create schedule
        schedule = CrawlSchedule(
            source_id=source.id,
            frequency_hours=frequency_hours,
            next_run_at=datetime.now(UTC),
        )
        self.db.add(schedule)

        # Create URL patterns
        if url_patterns:
            for pat in url_patterns:
                pattern = SourceURLPattern(
                    source_id=source.id,
                    url_pattern=pat["url_pattern"],
                    page_type=pat.get("page_type"),
                    follow_links=pat.get("follow_links", True),
                    link_selector=pat.get("link_selector"),
                    requires_javascript=pat.get("requires_javascript", False),
                    extraction_prompt_override=pat.get("extraction_prompt_override"),
                )
                self.db.add(pattern)

        await self.db.flush()
        logger.info("Created data source '%s' (id=%s)", name, source.id)
        return source

    async def get_source(self, source_id: UUID) -> DataSource:
        """Retrieve a single data source by ID."""
        source = await self.db.get(DataSource, source_id)
        if not source:
            raise NotFoundException(f"Data source {source_id} not found")
        return source

    async def list_sources(
        self,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[DataSource]:
        """List data sources, optionally filtered to active only."""
        stmt = select(DataSource).order_by(DataSource.created_at.desc()).limit(limit)
        if active_only:
            stmt = stmt.where(DataSource.is_active.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_source(self, source_id: UUID) -> None:
        """Soft-delete a data source by marking it inactive."""
        source = await self.get_source(source_id)
        source.is_active = False
        await self.db.flush()
        logger.info("Deactivated data source %s", source_id)

    # ------------------------------------------------------------------
    # Scheduling helpers
    # ------------------------------------------------------------------

    async def get_due_sources(self) -> list[DataSource]:
        """Return active sources whose scheduled crawl time has arrived.

        Filters: next_run_at <= now, is_enabled, consecutive_failures < max_retries.
        """
        now = datetime.now(UTC)
        stmt = (
            select(DataSource)
            .join(CrawlSchedule, CrawlSchedule.source_id == DataSource.id)
            .where(
                DataSource.is_active.is_(True),
                CrawlSchedule.is_enabled.is_(True),
                CrawlSchedule.next_run_at <= now,
                CrawlSchedule.consecutive_failures < CrawlSchedule.max_retries,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Health tracking
    # ------------------------------------------------------------------

    async def update_source_health(
        self,
        source_id: UUID,
        success: bool,
        pages_crawled: int = 0,
    ) -> None:
        """Update source reliability using exponential moving average.

        EMA formula: reliability = current * 0.8 + signal * 0.2
        """
        source = await self.get_source(source_id)

        signal = Decimal("1.0") if success else Decimal("0.0")
        current = source.reliability_score or Decimal("0.50")
        source.reliability_score = current * Decimal("0.8") + signal * Decimal("0.2")
        source.last_crawled_at = datetime.now(UTC)

        # Update schedule
        sched_result = await self.db.execute(
            select(CrawlSchedule).where(CrawlSchedule.source_id == source_id)
        )
        schedule = sched_result.scalar_one_or_none()
        if schedule:
            schedule.last_run_at = datetime.now(UTC)
            if success:
                schedule.consecutive_failures = 0
                schedule.next_run_at = datetime.now(UTC) + timedelta(hours=schedule.frequency_hours)
            else:
                schedule.consecutive_failures += 1
                # Exponential back-off: retry_delay_hours * 2^failures
                backoff = settings.crawler_retry_delay_hours * (2**schedule.consecutive_failures)
                schedule.next_run_at = datetime.now(UTC) + timedelta(hours=backoff)

        await self.db.flush()
        logger.info(
            "Source %s health updated: success=%s, reliability=%.2f",
            source_id,
            success,
            source.reliability_score,
        )

    # ------------------------------------------------------------------
    # Seed defaults
    # ------------------------------------------------------------------

    async def seed_default_sources(self) -> list[DataSource]:
        """Create a starter set of data sources for demonstration."""
        defaults = [
            {
                "name": "QS World University Rankings",
                "url": "https://www.topuniversities.com/university-rankings",
                "source_type": "ranking",
                "category": "ranking",
                "frequency_hours": 720,
                "url_patterns": [
                    {
                        "url_pattern": "/university-rankings/world-university-rankings/*",
                        "page_type": "ranking",
                    },
                ],
            },
            {
                "name": "US News Graduate Rankings",
                "url": "https://www.usnews.com/best-graduate-schools",
                "source_type": "ranking",
                "category": "ranking",
                "frequency_hours": 720,
                "url_patterns": [
                    {"url_pattern": "/best-graduate-schools/*", "page_type": "ranking"},
                ],
            },
            {
                "name": "Times Higher Education",
                "url": "https://www.timeshighereducation.com/world-university-rankings",
                "source_type": "ranking",
                "category": "ranking",
                "frequency_hours": 720,
                "url_patterns": [
                    {"url_pattern": "/world-university-rankings/*", "page_type": "ranking"},
                ],
            },
            {
                "name": "MIT Graduate Admissions",
                "url": "https://gradadmissions.mit.edu",
                "source_type": "university",
                "category": "program_data",
                "frequency_hours": 168,
                "url_patterns": [
                    {
                        "url_pattern": "/programs/*",
                        "page_type": "program_list",
                        "follow_links": True,
                    },
                    {"url_pattern": "/programs/*/", "page_type": "program_detail"},
                ],
            },
            {
                "name": "Stanford Graduate Programs",
                "url": "https://gradadmissions.stanford.edu",
                "source_type": "university",
                "category": "program_data",
                "frequency_hours": 168,
                "url_patterns": [
                    {
                        "url_pattern": "/programs/*",
                        "page_type": "program_list",
                        "follow_links": True,
                    },
                ],
            },
        ]

        created: list[DataSource] = []
        for cfg in defaults:
            try:
                source = await self.create_source(
                    name=cfg["name"],
                    url=cfg["url"],
                    source_type=cfg["source_type"],
                    category=cfg["category"],
                    frequency_hours=cfg["frequency_hours"],
                    url_patterns=cfg.get("url_patterns"),
                )
                created.append(source)
            except ConflictException:
                logger.debug("Default source '%s' already exists, skipping", cfg["name"])

        logger.info("Seeded %d default data sources", len(created))
        return created
