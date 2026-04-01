"""Tests for ModelTrainer — Phase 4 ML loop."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.ml.trainer import ModelTrainer
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import ModelRegistry, PredictionLog
from unipaith.models.ml_loop import OutcomeRecord, TrainingRun
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

# Feature columns the trainer expects
_FEATURE_KEYS = [
    "normalized_gpa",
    "work_experience_years",
    "research_count",
    "leadership_count",
    "publication_count",
    "total_activities",
    "test_score_avg",
    "embedding_similarity",
    "historical_fit",
    "institution_pref_fit",
    "student_pref_fit",
    "budget_fit",
]


async def _seed_training_outcomes(
    db: AsyncSession,
    count: int,
    admitted_ratio: float = 0.5,
) -> None:
    """Create outcome records with feature snapshots for training."""
    inst_user = User(
        id=uuid.uuid4(),
        email=f"inst-{uuid.uuid4().hex[:6]}@test.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id, name="Train U", type="university", country="US"
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="Train Program",
        degree_type="masters",
        is_published=True,
        tuition=45000,
    )
    db.add(program)
    await db.flush()

    for i in range(count):
        stu_user = User(
            id=uuid.uuid4(),
            email=f"train-{uuid.uuid4().hex[:6]}@test.com",
            cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
            role=UserRole.student,
            is_active=True,
        )
        db.add(stu_user)
        profile = StudentProfile(
            user_id=stu_user.id, first_name="T", last_name=str(i), nationality="US"
        )
        db.add(profile)
        await db.flush()

        is_positive = i < int(count * admitted_ratio)
        score = Decimal("0.85") if is_positive else Decimal("0.35")
        tier = 1 if is_positive else 3
        outcome_val = "admitted" if is_positive else "rejected"

        # Build a feature snapshot with all expected columns
        features = {}
        for k in _FEATURE_KEYS:
            if is_positive:
                features[k] = round(0.6 + (i % 5) * 0.08, 2)
            else:
                features[k] = round(0.2 + (i % 5) * 0.06, 2)

        pred = PredictionLog(
            student_id=profile.id,
            program_id=program.id,
            predicted_score=score,
            predicted_tier=tier,
            model_version="v1.0-mvp",
            features_used=features,
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
            features_snapshot=features,
            outcome_recorded_at=datetime.now(timezone.utc),
        )
        db.add(rec)

    await db.commit()


@pytest.mark.asyncio
async def test_insufficient_data(db_session: AsyncSession):
    """Seed < 50 outcomes, verify training run status='failed'."""
    await _seed_training_outcomes(db_session, count=20, admitted_ratio=0.5)

    trainer = ModelTrainer(db_session)
    run = await trainer.run_training(triggered_by="test")
    await db_session.commit()

    assert run.status == "failed"
    assert "Insufficient" in (run.failure_reason or "")


@pytest.mark.asyncio
async def test_training_runs(db_session: AsyncSession):
    """Seed 60 outcomes with feature snapshots, run training with minimal
    optuna trials, verify TrainingRun completed with test_metrics and
    ModelRegistry entry."""
    await _seed_training_outcomes(db_session, count=60, admitted_ratio=0.5)

    # Override optuna trials to keep test fast
    original_trials = settings.training_optuna_trials
    original_cv_folds = settings.training_cv_folds
    settings.training_optuna_trials = 2
    settings.training_cv_folds = 2

    try:
        trainer = ModelTrainer(db_session)
        run = await trainer.run_training(triggered_by="test")
        await db_session.commit()

        assert run.status == "completed"
        assert run.test_metrics is not None
        assert "accuracy" in run.test_metrics
        assert run.resulting_model_version is not None
        assert run.mode == "full"
        assert run.cv_metrics is not None
        assert run.cv_metrics.get("mode") == "full"

        # Verify ModelRegistry entry created
        result = await db_session.execute(
            select(ModelRegistry).where(
                ModelRegistry.model_version == run.resulting_model_version
            )
        )
        registry_entry = result.scalar_one_or_none()
        assert registry_entry is not None
        assert registry_entry.is_active is False
    finally:
        settings.training_optuna_trials = original_trials
        settings.training_cv_folds = original_cv_folds


@pytest.mark.asyncio
async def test_training_fast_mode_uses_fast_params(db_session: AsyncSession):
    """Fast mode should use fast tuning settings and persist mode metadata."""
    await _seed_training_outcomes(db_session, count=60, admitted_ratio=0.5)

    original_fast_trials = settings.training_fast_optuna_trials
    original_fast_cv = settings.training_fast_cv_folds
    settings.training_fast_optuna_trials = 1
    settings.training_fast_cv_folds = 2

    try:
        trainer = ModelTrainer(db_session)
        run = await trainer.run_training(triggered_by="test", mode="fast")
        await db_session.commit()

        assert run.status == "completed"
        assert run.mode == "fast"
        assert run.cv_metrics is not None
        assert run.cv_metrics.get("mode") == "fast"
        assert run.cv_metrics.get("mode_params", {}).get("optuna_trials") == 1
        assert run.cv_metrics.get("mode_params", {}).get("cv_folds") == 2
    finally:
        settings.training_fast_optuna_trials = original_fast_trials
        settings.training_fast_cv_folds = original_fast_cv
