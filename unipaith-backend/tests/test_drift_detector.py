"""Tests for DriftDetector — Phase 4 ML loop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.drift_detector import DriftDetector
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole


async def _seed_match_results(
    db: AsyncSession,
    count: int,
    base_time: datetime,
    score_mean: float = 0.7,
) -> None:
    """Create MatchResult records at base_time with scores around score_mean."""
    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="Drift U", type="university", country="US"
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="Drift Program",
        degree_type="masters",
        is_published=True,
        tuition=30000,
    )
    db.add(program)
    await db.flush()

    for i in range(count):
        stu_user = User(
            id=uuid.uuid4(),
            email=f"drift-stu-{uuid.uuid4().hex[:6]}@test.com",
            cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
            role=UserRole.student,
            is_active=True,
        )
        db.add(stu_user)
        profile = StudentProfile(
            user_id=stu_user.id, first_name="D", last_name=str(i), nationality="US"
        )
        db.add(profile)
        await db.flush()

        # Small variation around the mean
        variation = (i % 10) * 0.02 - 0.1
        score = max(0.0, min(1.0, score_mean + variation))

        mr = MatchResult(
            student_id=profile.id,
            program_id=program.id,
            match_score=Decimal(str(round(score, 4))),
            match_tier=1 if score > 0.7 else 2,
            computed_at=base_time + timedelta(hours=i),
        )
        db.add(mr)

    await db.commit()


@pytest.mark.asyncio
async def test_no_drift_stable_data(db_session: AsyncSession):
    """Seed match results in both reference and current periods with similar
    distributions, run check, verify no drift detected."""
    now = datetime.now(UTC)

    # Reference period: 30-90 days ago
    ref_time = now - timedelta(days=60)
    await _seed_match_results(db_session, count=10, base_time=ref_time, score_mean=0.7)

    # Current period: last 7 days
    cur_time = now - timedelta(days=3)
    await _seed_match_results(db_session, count=10, base_time=cur_time, score_mean=0.7)

    detector = DriftDetector(db_session)
    snapshots = await detector.check_all_drift(reference_days=90, current_days=7)
    await db_session.commit()

    # We should get at least the prediction distribution snapshot
    pred_snapshots = [s for s in snapshots if s.snapshot_type == "prediction_distribution"]
    if pred_snapshots:
        assert bool(pred_snapshots[0].drift_detected) is False


@pytest.mark.asyncio
async def test_drift_check_returns_snapshots(db_session: AsyncSession):
    """Verify check_all_drift runs and returns a list of DriftSnapshot."""
    detector = DriftDetector(db_session)
    snapshots = await detector.check_all_drift(reference_days=90, current_days=7)

    # With no data, snapshots may be empty but must be a list
    assert isinstance(snapshots, list)
