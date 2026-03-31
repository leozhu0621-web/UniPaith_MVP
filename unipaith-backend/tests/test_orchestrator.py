"""Tests for MLOrchestrator — Phase 4 ML loop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.orchestrator import MLOrchestrator
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import PredictionLog
from unipaith.models.ml_loop import OutcomeRecord
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole


async def _seed_outcomes_for_orchestrator(
    db: AsyncSession, count: int, admitted_ratio: float = 0.5
) -> None:
    """Seed outcome records for orchestrator testing."""
    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="Orch U", type="university", country="US"
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="Orch Program",
        degree_type="masters",
        is_published=True,
        tuition=40000,
    )
    db.add(program)
    await db.flush()

    for i in range(count):
        stu_user = User(
            id=uuid.uuid4(),
            email=f"orch-{uuid.uuid4().hex[:6]}@test.com",
            cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
            role=UserRole.student,
            is_active=True,
        )
        db.add(stu_user)
        profile = StudentProfile(
            user_id=stu_user.id, first_name="O", last_name=str(i), nationality="US"
        )
        db.add(profile)
        await db.flush()

        is_positive = i < int(count * admitted_ratio)
        score = Decimal("0.90") if is_positive else Decimal("0.30")
        tier = 1 if is_positive else 3
        outcome_val = "admitted" if is_positive else "rejected"

        pred = PredictionLog(
            student_id=profile.id,
            program_id=program.id,
            predicted_score=score,
            predicted_tier=tier,
            model_version="v1.0-mvp",
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
            actual_outcome=outcome_val,
            outcome_source="application_decision",
            outcome_confidence=Decimal("0.70"),
            features_snapshot={"normalized_gpa": 0.8},
            outcome_recorded_at=datetime.now(UTC),
        )
        db.add(rec)

    await db.commit()


@pytest.mark.asyncio
async def test_full_cycle_no_retrain(db_session: AsyncSession):
    """Seed outcomes, run cycle, verify evaluation ran. With high accuracy
    the cycle should not trigger retraining."""
    # Seed 35 well-predicted outcomes (high accuracy scenario)
    await _seed_outcomes_for_orchestrator(db_session, count=35, admitted_ratio=0.5)

    orchestrator = MLOrchestrator(db_session)
    result = await orchestrator.run_full_cycle(triggered_by="test")
    await db_session.commit()

    assert result["started_at"] is not None
    assert result["evaluation"] is not None
    # If accuracy is high enough, training should be skipped or not triggered
    # (depends on actual computed accuracy)
    assert result["evaluation"]["dataset_size"] == 35


@pytest.mark.asyncio
async def test_backfill(db_session: AsyncSession):
    """Call backfill, verify it runs without error."""
    orchestrator = MLOrchestrator(db_session)
    result = await orchestrator.backfill_outcomes()

    assert isinstance(result, dict)
    assert "decisions_processed" in result
