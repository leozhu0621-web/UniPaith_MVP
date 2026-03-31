"""Tests for ABTestManager — Phase 4 ML loop."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.ab_testing import ABTestManager
from unipaith.models.institution import Institution
from unipaith.models.matching import ModelRegistry
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole


async def _setup_models_and_student(
    db: AsyncSession,
) -> tuple[StudentProfile, ModelRegistry, ModelRegistry]:
    """Create active + challenger model and a student profile."""
    # Active model
    active = ModelRegistry(
        model_version="v1.0-active",
        architecture="XGBClassifier",
        performance_metrics={"accuracy": 0.80},
        is_active=True,
        trained_at=datetime.now(UTC),
    )
    db.add(active)

    # Challenger model
    challenger = ModelRegistry(
        model_version="v2.0-challenger",
        architecture="XGBClassifier",
        performance_metrics={"accuracy": 0.85},
        is_active=False,
        trained_at=datetime.now(UTC),
    )
    db.add(challenger)

    # Student
    stu_user = User(
        id=uuid.uuid4(),
        email=f"ab-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(stu_user)

    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="AB U", type="university", country="US"
    )
    db.add(institution)
    await db.flush()

    profile = StudentProfile(
        user_id=stu_user.id, first_name="AB", last_name="Test", nationality="US"
    )
    db.add(profile)
    await db.commit()

    return profile, active, challenger


@pytest.mark.asyncio
async def test_sticky_assignment(db_session: AsyncSession):
    """Get model twice for same student/experiment, verify same variant."""
    profile, active, challenger = await _setup_models_and_student(db_session)

    manager = ABTestManager(db_session)

    version1 = await manager.get_model_for_student(
        student_id=profile.id,
        experiment_name="exp-sticky-test",
    )
    await db_session.commit()

    version2 = await manager.get_model_for_student(
        student_id=profile.id,
        experiment_name="exp-sticky-test",
    )
    await db_session.commit()

    # Same student + same experiment = same model version (sticky)
    assert version1 == version2


@pytest.mark.asyncio
async def test_create_experiment(db_session: AsyncSession):
    """Create experiment, verify returned config."""
    _, active, challenger = await _setup_models_and_student(db_session)

    manager = ABTestManager(db_session)
    config = await manager.create_experiment(
        experiment_name="exp-test-create",
        challenger_version="v2.0-challenger",
        traffic_pct=0.20,
    )
    await db_session.commit()

    assert config["experiment_name"] == "exp-test-create"
    assert config["challenger"] == "v2.0-challenger"
    assert config["control"] == "v1.0-active"
    assert config["traffic_pct"] == 0.20
