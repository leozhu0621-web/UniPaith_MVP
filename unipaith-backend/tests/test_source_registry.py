"""Tests for Phase 5 – SourceRegistry."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.source_registry import SourceRegistry


async def test_create_source(db_session: AsyncSession):
    registry = SourceRegistry(db_session)
    source = await registry.create_source(
        name="Test Uni",
        url="https://test-uni.edu",
        source_type="university_website",
        category="programs",
        frequency_hours=24,
    )
    await db_session.commit()

    assert source.id is not None
    assert source.source_name == "Test Uni"
    assert source.is_active is True


async def test_list_sources(db_session: AsyncSession):
    registry = SourceRegistry(db_session)
    await registry.create_source(
        name="Source A",
        url="https://a.edu",
        source_type="university_website",
        category="programs",
        frequency_hours=24,
    )
    await registry.create_source(
        name="Source B",
        url="https://b.edu",
        source_type="university_website",
        category="programs",
        frequency_hours=48,
    )
    await db_session.commit()

    sources = await registry.list_sources(active_only=True)
    assert len(sources) >= 2


async def test_seed_defaults(db_session: AsyncSession):
    registry = SourceRegistry(db_session)
    sources = await registry.seed_default_sources()
    await db_session.commit()

    assert len(sources) > 0
    # All should be active
    for s in sources:
        assert s.is_active is True
