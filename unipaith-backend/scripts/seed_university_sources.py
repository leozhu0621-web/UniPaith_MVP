"""
Seed the crawler with real university sources, URL patterns, and crawl schedules.

Creates DataSource + CrawlSchedule + SourceURLPattern for each university
so the crawler engine can find and process them.

Usage:
    cd unipaith-backend
    PYTHONPATH=src .venv/bin/python -m scripts.seed_university_sources
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

SEED_FILE = Path(__file__).parent.parent / "data" / "university_seeds.json"


async def main():
    from sqlalchemy import select

    from unipaith.database import async_session
    from unipaith.models.crawler import CrawlSchedule, SourceURLPattern
    from unipaith.models.matching import DataSource

    seeds = json.loads(SEED_FILE.read_text())
    logger.info("Loaded %d university seeds", len(seeds))

    async with async_session() as db:
        created = 0
        skipped = 0

        for seed in seeds:
            # Check if source already exists by name
            existing = await db.execute(
                select(DataSource).where(DataSource.source_name == seed["name"])
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Create the data source
            source = DataSource(
                source_name=seed["name"],
                source_url=seed["base_url"],
                source_type="university_website",
                data_category="program_data",
                crawl_frequency="168",
                is_active=True,
            )
            db.add(source)
            await db.flush()

            # Create crawl schedule — first run immediately, then weekly
            schedule = CrawlSchedule(
                source_id=source.id,
                frequency_hours=168,  # weekly
                next_run_at=datetime.now(timezone.utc),  # due now
                is_enabled=True,
            )
            db.add(schedule)

            # Create URL patterns from seed program_urls
            for url in seed.get("program_urls", []):
                pattern = SourceURLPattern(
                    source_id=source.id,
                    url_pattern=url,
                    page_type="program_list",
                    follow_links=True,
                )
                db.add(pattern)

            created += 1
            logger.info("  Created source: %s (%d URLs)", seed["name"], len(seed.get("program_urls", [])))

        await db.commit()
        logger.info("Done: %d sources created, %d already existed", created, skipped)


if __name__ == "__main__":
    asyncio.run(main())
