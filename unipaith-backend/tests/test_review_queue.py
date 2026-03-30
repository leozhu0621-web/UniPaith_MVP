"""Tests for Phase 5 – ReviewQueue."""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.review_queue import ReviewQueue
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.matching import DataSource, RawIngestedData
from unipaith.models.user import User




async def _seed_source(db: AsyncSession) -> DataSource:
    source = DataSource(
        source_name="Test University",
        source_url="https://example-university.edu",
        source_type="university_website",
        data_category="programs",
        is_active=True,
    )
    db.add(source)
    await db.commit()
    return source


async def _seed_pending_ep(
    db: AsyncSession, source: DataSource, name: str = "Program A"
) -> ExtractedProgram:
    job = CrawlJob(source_id=source.id, status="completed")
    db.add(job)
    await db.flush()

    raw = RawIngestedData(
        source_id=source.id,
        raw_content="<html>test</html>",
        content_hash=f"hash-{uuid.uuid4().hex[:8]}",
        processed=False,
    )
    db.add(raw)
    await db.flush()

    ep = ExtractedProgram(
        crawl_job_id=job.id,
        source_id=source.id,
        raw_data_id=raw.id,
        source_url=f"https://example.edu/programs/{name.lower().replace(' ', '-')}",
        institution_name="Test University",
        program_name=name,
        degree_type="Masters",
        extraction_confidence=Decimal("0.65"),
        match_type="new",
        review_status="pending",
    )
    db.add(ep)
    await db.flush()
    return ep


async def test_list_pending(db_session: AsyncSession):
    source = await _seed_source(db_session)
    await _seed_pending_ep(db_session, source, "Program A")
    await _seed_pending_ep(db_session, source, "Program B")
    await db_session.commit()

    queue = ReviewQueue(db_session)
    items = await queue.list_pending()
    assert len(items) >= 2


async def test_approve(db_session: AsyncSession, mock_admin_user: User):
    source = await _seed_source(db_session)
    ep = await _seed_pending_ep(db_session, source, "To Approve")
    await db_session.commit()

    queue = ReviewQueue(db_session)
    result = await queue.approve(
        extracted_id=ep.id,
        reviewer_id=mock_admin_user.id,
        notes="Looks good",
    )

    # approve() ingests after approving, so status becomes auto_ingested
    assert ep.review_status in ("approved", "auto_ingested")
    assert ep.reviewed_by == mock_admin_user.id


async def test_reject(db_session: AsyncSession, mock_admin_user: User):
    source = await _seed_source(db_session)
    ep = await _seed_pending_ep(db_session, source, "To Reject")
    await db_session.commit()

    queue = ReviewQueue(db_session)
    result = await queue.reject(
        extracted_id=ep.id,
        reviewer_id=mock_admin_user.id,
        reason="Bad data",
    )

    assert ep.review_status == "rejected"
    assert ep.reviewed_by == mock_admin_user.id
