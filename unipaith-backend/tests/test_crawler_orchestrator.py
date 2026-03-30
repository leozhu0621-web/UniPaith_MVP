"""Tests for Phase 5 – CrawlerOrchestrator."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.orchestrator import CrawlerOrchestrator




async def test_run_scheduled_no_due(db_session: AsyncSession):
    """No due sources means empty results."""
    orchestrator = CrawlerOrchestrator(db_session)
    result = await orchestrator.run_scheduled_crawls()

    assert result["sources_processed"] == 0
    assert result["results"] == []


async def test_crawl_single_url(db_session: AsyncSession):
    """crawl_single_url should not crash even with no matching source."""
    orchestrator = CrawlerOrchestrator(db_session)
    result = await orchestrator.crawl_single_url(
        url="https://example.edu/programs",
        source_id=None,
    )
    # Should return some dict without raising
    assert isinstance(result, dict)
