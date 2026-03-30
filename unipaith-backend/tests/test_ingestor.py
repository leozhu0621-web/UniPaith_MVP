"""Tests for Phase 5 – AutoIngestor."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.ingestor import AutoIngestor
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.institution import Institution, Program
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


async def _seed_institution(db: AsyncSession, inst_user: User) -> Institution:
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id,
        name="Test University",
        type="university",
        country="US",
    )
    db.add(institution)
    await db.flush()
    return institution


async def _seed_ep(
    db: AsyncSession,
    source: DataSource,
    confidence: Decimal,
    match_type: str = "new",
    matched_institution_id=None,
) -> ExtractedProgram:
    job = CrawlJob(source_id=source.id, status="completed")
    db.add(job)
    await db.flush()

    raw = RawIngestedData(
        source_id=source.id,
        raw_content="<html>test</html>",
        content_hash="hash123",
        processed=False,
    )
    db.add(raw)
    await db.flush()

    ep = ExtractedProgram(
        crawl_job_id=job.id,
        source_id=source.id,
        raw_data_id=raw.id,
        source_url="https://example-university.edu/programs/test",
        institution_name="Test University",
        institution_country="US",
        program_name="Test Program MS",
        degree_type="Masters",
        extraction_confidence=confidence,
        match_type=match_type,
        matched_institution_id=matched_institution_id,
    )
    db.add(ep)
    await db.flush()
    return ep


async def test_high_confidence_auto_ingest(
    db_session: AsyncSession, mock_institution_user: User
):
    """High confidence + new + matched institution -> auto_ingested."""
    source = await _seed_source(db_session)
    institution = await _seed_institution(db_session, mock_institution_user)
    ep = await _seed_ep(
        db_session, source, Decimal("0.90"), "new",
        matched_institution_id=institution.id,
    )

    ingestor = AutoIngestor(db_session)
    result = await ingestor.process_extracted(ep.id)

    assert ep.review_status == "auto_ingested"
    assert result["action"] != "queued_for_review"


async def test_low_confidence_queued(db_session: AsyncSession):
    """Low confidence -> pending review."""
    source = await _seed_source(db_session)
    ep = await _seed_ep(db_session, source, Decimal("0.60"), "new")

    ingestor = AutoIngestor(db_session)
    result = await ingestor.process_extracted(ep.id)

    assert ep.review_status == "pending"
    assert result["action"] == "queued_for_review"
