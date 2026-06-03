"""Spec 67 §2/§6 — consent-gated outcome ingestion (closes gap-audit G-T2).

The hard gate: a student with consent.training=false contributes to NO training
set (46 §9). Proven by asserting the row count stays 0 when consent is withheld.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.learning_loop import LearningLoopService


async def _seed(db: AsyncSession, student_user: User, inst_user: User):
    db.add(student_user)
    db.add(inst_user)
    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)
    inst = Institution(
        admin_user_id=inst_user.id, name="Test U", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id, program_name="CS Masters", degree_type="masters", is_published=True
    )
    db.add(program)
    await db.flush()
    return profile, program


@pytest.mark.asyncio
async def test_records_pair_with_consent(
    db_session: AsyncSession, mock_student_user, mock_institution_user
):
    profile, program = await _seed(db_session, mock_student_user, mock_institution_user)
    svc = LearningLoopService(db_session)
    pair = await svc.record_confidence_outcome(
        student_id=profile.id,
        program_id=program.id,
        predicted_confidence=0.82,
        outcome=1,
        outcome_kind="enrolled",
        training_consent=True,
    )
    assert pair is not None
    assert await svc.confidence_pair_count() == 1


@pytest.mark.asyncio
async def test_consent_training_false_records_nothing(
    db_session: AsyncSession, mock_student_user, mock_institution_user
):
    profile, program = await _seed(db_session, mock_student_user, mock_institution_user)
    svc = LearningLoopService(db_session)
    result = await svc.record_confidence_outcome(
        student_id=profile.id,
        program_id=program.id,
        predicted_confidence=0.9,
        outcome=1,
        outcome_kind="enrolled",
        training_consent=False,  # 46 §9 hard gate
    )
    assert result is None
    assert await svc.confidence_pair_count() == 0  # nothing entered the training set


@pytest.mark.asyncio
async def test_invalid_outcome_rejected(
    db_session: AsyncSession, mock_student_user, mock_institution_user
):
    profile, program = await _seed(db_session, mock_student_user, mock_institution_user)
    svc = LearningLoopService(db_session)
    with pytest.raises(ValueError):
        await svc.record_confidence_outcome(
            student_id=profile.id,
            program_id=program.id,
            predicted_confidence=0.5,
            outcome=2,  # must be 0 or 1
            outcome_kind="applied",
            training_consent=True,
        )


@pytest.mark.asyncio
async def test_calibrator_not_ready_below_threshold(
    db_session: AsyncSession, mock_student_user, mock_institution_user
):
    profile, program = await _seed(db_session, mock_student_user, mock_institution_user)
    svc = LearningLoopService(db_session)
    await svc.record_confidence_outcome(
        student_id=profile.id,
        program_id=program.id,
        predicted_confidence=0.7,
        outcome=0,
        outcome_kind="aged_out",  # window passed without the positive event
        training_consent=True,
    )
    # One real pair is far below the fit threshold — Confidence stays honest-uncalibrated.
    assert await svc.calibrator_ready() is False


@pytest.mark.asyncio
async def test_invalid_outcome_kind_rejected(
    db_session: AsyncSession, mock_student_user, mock_institution_user
):
    profile, program = await _seed(db_session, mock_student_user, mock_institution_user)
    svc = LearningLoopService(db_session)
    with pytest.raises(ValueError):
        await svc.record_confidence_outcome(
            student_id=profile.id,
            program_id=program.id,
            predicted_confidence=0.5,
            outcome=1,
            outcome_kind="rejected",  # not in the allowed CHECK set
            training_consent=True,
        )
