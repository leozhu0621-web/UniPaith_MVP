"""Tests for Phase 5 – EnrichmentPipeline."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.enrichment import EnrichmentPipeline
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import DataSource
from unipaith.models.user import User


async def _seed_source(db: AsyncSession) -> DataSource:
    source = DataSource(
        source_name="Enrichment Source",
        source_url="https://rankings.example.com",
        source_type="ranking_site",
        data_category="rankings",
        is_active=True,
    )
    db.add(source)
    await db.commit()
    return source


async def _seed_institution_and_program(
    db: AsyncSession, inst_user: User
) -> tuple[Institution, Program]:
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id,
        name="MIT",
        type="university",
        country="US",
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


async def test_create_enrichment(db_session: AsyncSession, mock_institution_user: User):
    source = await _seed_source(db_session)
    institution, program = await _seed_institution_and_program(db_session, mock_institution_user)

    pipeline = EnrichmentPipeline(db_session)
    record = await pipeline.enrich_program(
        program_id=program.id,
        enrichment_type="stats",
        source_id=source.id,
        data={"acceptance_rate": 0.12},
        confidence=0.85,
    )
    await db_session.commit()

    assert record.id is not None
    assert record.enrichment_type == "stats"
    assert record.program_id == program.id


async def test_apply_enrichments(db_session: AsyncSession, mock_institution_user: User):
    source = await _seed_source(db_session)
    institution, program = await _seed_institution_and_program(db_session, mock_institution_user)

    pipeline = EnrichmentPipeline(db_session)
    await pipeline.enrich_program(
        program_id=program.id,
        enrichment_type="stats",
        source_id=source.id,
        data={"acceptance_rate": 0.15},
        confidence=0.90,
    )
    await db_session.commit()

    result = await pipeline.apply_enrichments(program.id)
    assert result["applied"] >= 1
