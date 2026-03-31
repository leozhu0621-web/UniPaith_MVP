"""Tests for FairnessChecker — Phase 4 ML loop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.fairness import FairnessChecker
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import PredictionLog
from unipaith.models.ml_loop import OutcomeRecord
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole


async def _seed_fairness_outcomes(
    db: AsyncSession,
    nationalities: dict[str, tuple[int, int]],
    model_version: str = "v1.0-mvp",
) -> list[dict]:
    """Seed outcomes for fairness testing.

    nationalities maps nationality -> (admitted_count, rejected_count).
    Returns the outcomes list suitable for FairnessChecker.run_fairness_check.
    """
    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="Fair U", type="university", country="US"
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="Fair Program",
        degree_type="masters",
        is_published=True,
        tuition=35000,
    )
    db.add(program)
    await db.flush()

    outcomes: list[dict] = []

    for nationality, (admitted, rejected) in nationalities.items():
        for i in range(admitted + rejected):
            is_positive = i < admitted
            stu_user = User(
                id=uuid.uuid4(),
                email=f"fair-{uuid.uuid4().hex[:6]}@test.com",
                cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
                role=UserRole.student,
                is_active=True,
            )
            db.add(stu_user)
            profile = StudentProfile(
                user_id=stu_user.id,
                first_name="F",
                last_name=str(i),
                nationality=nationality,
            )
            db.add(profile)
            await db.flush()

            score = 0.85 if is_positive else 0.35
            tier = 1 if is_positive else 3
            outcome_val = "admitted" if is_positive else "rejected"

            pred = PredictionLog(
                student_id=profile.id,
                program_id=program.id,
                predicted_score=Decimal(str(score)),
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
                predicted_score=Decimal(str(score)),
                predicted_tier=tier,
                actual_outcome=outcome_val,
                outcome_source="application_decision",
                outcome_confidence=Decimal("0.70"),
                outcome_recorded_at=datetime.now(UTC),
            )
            db.add(rec)

            outcomes.append(
                {
                    "predicted_score": score,
                    "predicted_tier": tier,
                    "actual_outcome": outcome_val,
                    "outcome_confidence": 0.70,
                    "student_id": str(profile.id),
                    "program_id": str(program.id),
                }
            )

    await db.commit()
    return outcomes


@pytest.mark.asyncio
async def test_fairness_equal_groups(db_session: AsyncSession):
    """Seed outcomes with equal admit rates across nationalities -> passed=True."""
    outcomes = await _seed_fairness_outcomes(
        db_session,
        nationalities={
            "US": (5, 5),
            "IN": (5, 5),
        },
    )

    checker = FairnessChecker(db_session)
    reports = await checker.run_fairness_check(
        model_version="v1.0-mvp",
        outcomes=outcomes,
    )
    await db_session.commit()

    # nationality check should pass since rates are equal
    nat_reports = [r for r in reports if r.protected_attribute == "nationality"]
    assert len(nat_reports) == 1
    assert nat_reports[0].passed is True


@pytest.mark.asyncio
async def test_fairness_large_disparity(db_session: AsyncSession):
    """Seed outcomes with very different rates -> passed=False."""
    outcomes = await _seed_fairness_outcomes(
        db_session,
        nationalities={
            "US": (9, 1),  # 90% positive rate
            "IN": (1, 9),  # 10% positive rate
        },
    )

    checker = FairnessChecker(db_session)
    reports = await checker.run_fairness_check(
        model_version="v1.0-mvp",
        outcomes=outcomes,
    )
    await db_session.commit()

    nat_reports = [r for r in reports if r.protected_attribute == "nationality"]
    assert len(nat_reports) == 1
    assert nat_reports[0].passed is False
    assert float(nat_reports[0].demographic_parity_diff) >= 0.5
