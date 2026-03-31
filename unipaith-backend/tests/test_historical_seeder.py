"""Tests for Phase 5 – HistoricalSeeder."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.historical_seeder import HistoricalSeeder
from unipaith.models.application import HistoricalOutcome
from unipaith.models.institution import Institution, Program
from unipaith.models.user import User


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


async def test_seed_from_extracted(db_session: AsyncSession, mock_institution_user: User):
    institution, program = await _seed_institution_and_program(db_session, mock_institution_user)

    stats_data = [
        {"year": 2023, "applicants": 500, "admitted": 50, "enrolled": 30},
        {"year": 2024, "applicants": 600, "admitted": 55, "enrolled": 35},
    ]

    seeder = HistoricalSeeder(db_session)
    created = await seeder.seed_from_extracted(program.id, stats_data)
    await db_session.commit()

    assert created == 2

    result = await db_session.execute(
        select(HistoricalOutcome).where(HistoricalOutcome.program_id == program.id)
    )
    records = list(result.scalars().all())
    assert len(records) == 2


async def test_empty_stats(db_session: AsyncSession, mock_institution_user: User):
    institution, program = await _seed_institution_and_program(db_session, mock_institution_user)

    seeder = HistoricalSeeder(db_session)
    created = await seeder.seed_from_extracted(program.id, [])
    assert created == 0
