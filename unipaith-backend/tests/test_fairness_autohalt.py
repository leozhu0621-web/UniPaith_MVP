"""Fairness disparate-impact auto-halt (gap audit G-I5 / G-T3 / Spec 43 §6).

Contract: when the matching model's disparate-impact delta breaches threshold
(default 0.20) for two consecutive weeks, the program's matching is halted and
the matcher stops scoring new applicants until a human overrides.
"""

from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.fairness_service import FairnessService


async def _seed_program(db: AsyncSession) -> Program:
    admin = User(
        id=uuid4(),
        email=f"inst-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="FairU", type="university", country="US")
    db.add(inst)
    await db.flush()
    program = Program(institution_id=inst.id, program_name="Fair Test MS", degree_type="masters")
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return program


async def _seed_match(db, program_id, *, gender, fitness, computed_at):
    user = User(
        id=uuid4(),
        email=f"s-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id, gender_identity=gender)
    db.add(profile)
    await db.flush()
    db.add(
        MatchResult(
            student_id=profile.id,
            program_id=program_id,
            fitness_score=Decimal(str(fitness)),
            confidence_score=Decimal("0.7"),
            computed_at=computed_at,
        )
    )


async def _seed_week(db, program_id, week_start, *, male_fitness, female_fitness):
    """5 male + 5 female students with the given fitness, matched in `week_start`."""
    when = _dt.datetime(week_start.year, week_start.month, week_start.day, 12, tzinfo=_dt.UTC)
    for _ in range(5):
        await _seed_match(db, program_id, gender="male", fitness=male_fitness, computed_at=when)
        await _seed_match(db, program_id, gender="female", fitness=female_fitness, computed_at=when)
    await db.commit()


@pytest.mark.asyncio
async def test_two_breached_weeks_halt_matching(db_session: AsyncSession):
    program = await _seed_program(db_session)
    svc = FairnessService(db_session)

    week1 = _dt.date(2026, 5, 4)
    week2 = _dt.date(2026, 5, 11)
    # Males recommended (fitness 0.9), females not (fitness 0.1): delta ~1.0.
    await _seed_week(db_session, program.id, week1, male_fitness=0.9, female_fitness=0.1)
    await _seed_week(db_session, program.id, week2, male_fitness=0.9, female_fitness=0.1)

    sigs1 = await svc.compute_weekly_signals(program.id, week1)
    sigs2 = await svc.compute_weekly_signals(program.id, week2)
    await db_session.commit()

    gender_sig = next(s for s in sigs1 if s.protected_attribute == "gender_identity")
    assert gender_sig.disparate_impact_delta > 0.20
    assert gender_sig.breached is True
    assert any(s.protected_attribute == "gender_identity" for s in sigs2)

    halted = await svc.evaluate_auto_halt(program.id)
    await db_session.commit()
    assert halted is True
    await db_session.refresh(program)
    assert program.matching_halted is True


@pytest.mark.asyncio
async def test_single_breached_week_does_not_halt(db_session: AsyncSession):
    program = await _seed_program(db_session)
    svc = FairnessService(db_session)
    week1 = _dt.date(2026, 5, 4)
    await _seed_week(db_session, program.id, week1, male_fitness=0.9, female_fitness=0.1)
    await svc.compute_weekly_signals(program.id, week1)
    await db_session.commit()
    halted = await svc.evaluate_auto_halt(program.id)
    await db_session.commit()
    assert halted is False
    await db_session.refresh(program)
    assert program.matching_halted is False


@pytest.mark.asyncio
async def test_fair_program_not_halted(db_session: AsyncSession):
    program = await _seed_program(db_session)
    svc = FairnessService(db_session)
    week1 = _dt.date(2026, 5, 4)
    week2 = _dt.date(2026, 5, 11)
    # Balanced selection across groups -> delta ~0.
    await _seed_week(db_session, program.id, week1, male_fitness=0.8, female_fitness=0.8)
    await _seed_week(db_session, program.id, week2, male_fitness=0.8, female_fitness=0.8)
    sigs = await svc.compute_weekly_signals(program.id, week1)
    await svc.compute_weekly_signals(program.id, week2)
    await db_session.commit()
    gender_sig = next(s for s in sigs if s.protected_attribute == "gender_identity")
    assert gender_sig.breached is False
    halted = await svc.evaluate_auto_halt(program.id)
    assert halted is False


@pytest.mark.asyncio
async def test_override_clears_halt(db_session: AsyncSession):
    program = await _seed_program(db_session)
    program.matching_halted = True
    await db_session.commit()
    svc = FairnessService(db_session)
    result = await svc.override_halt(program.id)
    await db_session.commit()
    assert result is not None
    await db_session.refresh(program)
    assert program.matching_halted is False
