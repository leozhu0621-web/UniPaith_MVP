"""Knowledge engine loop: bootstrap frontier and persisted snapshot."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from unipaith.crawler.source_discoverer import SourceDiscoverer
from unipaith.models.knowledge import CrawlFrontier, EngineLoopSnapshot
from unipaith.services.engine_loop import EngineLoop, get_engine_state


@pytest.mark.asyncio
async def test_bootstrap_adds_urls_when_frontier_empty(db_session):
    discoverer = SourceDiscoverer(db_session)
    added = await discoverer.ensure_bootstrap_frontier(
        ["https://www.ed.gov/news/press-releases"],
    )
    assert added >= 1
    pending = await db_session.scalar(
        select(func.count()).select_from(CrawlFrontier).where(CrawlFrontier.status == "pending")
    )
    assert (pending or 0) >= 1


@pytest.mark.asyncio
async def test_persist_snapshot_when_paused(db_session):
    state = get_engine_state()
    prev = state.paused
    try:
        state.paused = True
        loop = EngineLoop(db_session)
        result = await loop.run_tick()
        await db_session.commit()
        assert result.get("status") == "paused"
        row = await db_session.get(EngineLoopSnapshot, 1)
        assert row is not None
        assert row.tick_status == "paused"
    finally:
        state.paused = prev
