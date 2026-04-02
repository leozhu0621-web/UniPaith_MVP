"""Tests for OutcomeCollector — Phase 4 ML loop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.outcome_collector import OutcomeCollector
from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import PredictionLog
from unipaith.models.ml_loop import OutcomeRecord
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole


async def _seed_prediction_with_outcome(
    db: AsyncSession, student_user: User, outcome: str = "admitted"
) -> tuple:
    """Seed a student, program, prediction log, application with decision."""
    db.add(student_user)
    profile = StudentProfile(
        user_id=student_user.id, first_name="Test", last_name="Student", nationality="US"
    )
    db.add(profile)

    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="Test U", type="university", country="US"
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.flush()

    prediction = PredictionLog(
        student_id=profile.id,
        program_id=program.id,
        predicted_score=Decimal("0.85"),
        predicted_tier=1,
        model_version="v1.0-mvp",
        features_used={"structured": {"normalized_gpa": 0.9}},
    )
    db.add(prediction)

    app = Application(
        student_id=profile.id,
        program_id=program.id,
        status="submitted",
        decision=outcome,
        decision_at=datetime.now(UTC),
    )
    db.add(app)
    await db.commit()
    return profile, program, prediction, app, institution


@pytest.mark.asyncio
async def test_record_application_decision(db_session: AsyncSession, mock_student_user: User):
    """Seed prediction + app with decision, call record_application_decision,
    verify OutcomeRecord created with confidence 0.70."""
    profile, program, prediction, app, _ = await _seed_prediction_with_outcome(
        db_session, mock_student_user, outcome="admitted"
    )

    collector = OutcomeCollector(db_session)
    record = await collector.record_application_decision(app.id)
    await db_session.commit()

    assert record is not None
    assert record.actual_outcome == "admitted"
    assert record.outcome_confidence == Decimal("0.70")
    assert record.outcome_source == "application_decision"
    assert record.prediction_log_id == prediction.id


@pytest.mark.asyncio
async def test_no_duplicate(db_session: AsyncSession, mock_student_user: User):
    """Call record_application_decision twice, verify only 1 OutcomeRecord."""
    _, _, _, app, _ = await _seed_prediction_with_outcome(
        db_session, mock_student_user, outcome="admitted"
    )

    collector = OutcomeCollector(db_session)
    first = await collector.record_application_decision(app.id)
    await db_session.commit()

    second = await collector.record_application_decision(app.id)
    await db_session.commit()

    # Both should return the same record (dedup)
    assert first is not None
    assert second is not None
    assert first.id == second.id

    result = await db_session.execute(select(OutcomeRecord))
    all_records = result.scalars().all()
    assert len(all_records) == 1


@pytest.mark.asyncio
async def test_backfill(db_session: AsyncSession):
    """Seed 2 apps with decisions, call backfill_outcomes, verify counts."""
    # Seed 2 student+prediction+app combos
    for i in range(2):
        user = User(
            id=uuid.uuid4(),
            email=f"student-{i}-{uuid.uuid4().hex[:6]}@test.com",
            cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
            role=UserRole.student,
            is_active=True,
        )
        await _seed_prediction_with_outcome(
            db_session, user, outcome="admitted" if i == 0 else "rejected"
        )

    collector = OutcomeCollector(db_session)
    counts = await collector.backfill_outcomes()
    await db_session.commit()

    assert counts["decisions_processed"] == 2

    result = await db_session.execute(select(OutcomeRecord))
    all_records = result.scalars().all()
    assert len(all_records) == 2
