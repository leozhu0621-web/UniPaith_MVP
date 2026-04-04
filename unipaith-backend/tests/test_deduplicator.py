"""Tests for Phase 5 – Deduplicator."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.deduplicator import Deduplicator
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
    await db.flush()
    return source


async def _seed_crawl_job(db: AsyncSession, source: DataSource) -> CrawlJob:
    job = CrawlJob(source_id=source.id, status="completed")
    db.add(job)
    await db.flush()
    return job


async def _seed_raw_data(db: AsyncSession, source: DataSource) -> RawIngestedData:
    raw = RawIngestedData(
        source_id=source.id,
        raw_content="<html>test</html>",
        content_hash="abc123",
        processed=False,
    )
    db.add(raw)
    await db.flush()
    return raw


async def _seed_institution_and_program(db: AsyncSession, inst_user: User):
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="MIT", type="university", country="US"
    )
    db.add(institution)
    await db.flush()
    program = Program(
        institution_id=institution.id,
        program_name="Computer Science MS",
        degree_type="masters",
        is_published=True,
        tuition=55000,
    )
    db.add(program)
    await db.commit()
    return institution, program


async def test_no_match_new(db_session: AsyncSession):
    """ExtractedProgram with unknown institution should get match_type='new'."""
    source = await _seed_source(db_session)
    job = await _seed_crawl_job(db_session, source)
    raw = await _seed_raw_data(db_session, source)

    ep = ExtractedProgram(
        crawl_job_id=job.id,
        source_id=source.id,
        raw_data_id=raw.id,
        source_url="https://unknown-uni.edu/programs",
        institution_name="Nonexistent University",
        program_name="Basket Weaving PhD",
        degree_type="PhD",
        extraction_confidence=Decimal("0.85"),
    )
    db_session.add(ep)
    await db_session.flush()

    dedup = Deduplicator(db_session)
    result = await dedup.match_and_classify(ep.id)
    assert result.match_type == "new"
    assert result.matched_institution_id is None


async def test_exact_match(db_session: AsyncSession, mock_institution_user: User):
    """ExtractedProgram matching existing institution+program should be 'duplicate' or 'update'."""
    source = await _seed_source(db_session)
    institution, program = await _seed_institution_and_program(db_session, mock_institution_user)
    job = await _seed_crawl_job(db_session, source)
    raw = await _seed_raw_data(db_session, source)

    ep = ExtractedProgram(
        crawl_job_id=job.id,
        source_id=source.id,
        raw_data_id=raw.id,
        source_url="https://mit.edu/programs/cs",
        institution_name="MIT",
        institution_country="US",
        program_name="Computer Science MS",
        degree_type="Masters",
        extraction_confidence=Decimal("0.90"),
    )
    db_session.add(ep)
    await db_session.flush()

    dedup = Deduplicator(db_session)
    result = await dedup.match_and_classify(ep.id)
    assert result.match_type in ("duplicate", "update")
    assert result.matched_institution_id == institution.id
