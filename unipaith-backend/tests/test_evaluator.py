"""Tests for ModelEvaluator — Phase 4 ML loop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException
from unipaith.ml.evaluator import ModelEvaluator
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import PredictionLog
from unipaith.models.ml_loop import OutcomeRecord
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole


async def _seed_outcomes(
    db: AsyncSession,
    count: int,
    model_version: str = "v1.0-mvp",
    admitted_ratio: float = 0.5,
) -> None:
    """Create count OutcomeRecord entries linked to PredictionLog."""
    # Create shared institution + program
    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="Eval U", type="university", country="US"
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="Test Program",
        degree_type="masters",
        is_published=True,
        tuition=40000,
    )
    db.add(program)
    await db.flush()

    for i in range(count):
        stu_user = User(
            id=uuid.uuid4(),
            email=f"stu-{uuid.uuid4().hex[:6]}@test.com",
            cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
            role=UserRole.student,
            is_active=True,
        )
        db.add(stu_user)
        profile = StudentProfile(
            user_id=stu_user.id, first_name="S", last_name=str(i), nationality="US"
        )
        db.add(profile)
        await db.flush()

        is_positive = i < int(count * admitted_ratio)
        score = Decimal("0.90") if is_positive else Decimal("0.40")
        tier = 1 if is_positive else 3
        outcome = "admitted" if is_positive else "rejected"

        pred = PredictionLog(
            student_id=profile.id,
            program_id=program.id,
            predicted_score=score,
            predicted_tier=tier,
            model_version=model_version,
            features_used={"normalized_gpa": 0.8},
        )
        db.add(pred)
        await db.flush()

        rec = OutcomeRecord(
            prediction_log_id=pred.id,
            student_id=profile.id,
            program_id=program.id,
            predicted_score=score,
            predicted_tier=tier,
            actual_outcome=outcome,
            outcome_source="application_decision",
            outcome_confidence=Decimal("0.70"),
            features_snapshot={"normalized_gpa": 0.8},
            outcome_recorded_at=datetime.now(UTC),
        )
        db.add(rec)

    await db.commit()


@pytest.mark.asyncio
async def test_basic_evaluation(db_session: AsyncSession):
    """Seed 35 outcome records, run evaluation, verify EvaluationRun created."""
    await _seed_outcomes(db_session, count=35, admitted_ratio=0.5)

    evaluator = ModelEvaluator(db_session)
    eval_run = await evaluator.run_evaluation(model_version="v1.0-mvp")
    await db_session.commit()

    assert eval_run is not None
    assert eval_run.model_version == "v1.0-mvp"
    assert eval_run.dataset_size == 35
    assert "accuracy" in eval_run.metrics
    assert "f1" in eval_run.metrics
    assert eval_run.metrics["accuracy"] >= 0.0


@pytest.mark.asyncio
async def test_insufficient_data(db_session: AsyncSession):
    """Seed < 30 outcomes, verify BadRequestException raised."""
    await _seed_outcomes(db_session, count=10, admitted_ratio=0.5)

    evaluator = ModelEvaluator(db_session)
    with pytest.raises(BadRequestException, match="Insufficient"):
        await evaluator.run_evaluation(model_version="v1.0-mvp")
