"""Admin-only endpoints for the ML self-improving loop.

Provides 17 endpoints covering:
- Full cycle / evaluation / drift / backfill triggers
- Evaluation and training run history
- Model registry management (list, promote, rollback)
- A/B test creation and evaluation
- Drift and fairness reports
- Outcome statistics
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.ml.ab_testing import ABTestManager
from unipaith.ml.model_manager import ModelManager
from unipaith.ml.orchestrator import MLOrchestrator
from unipaith.ml.trainer import ModelTrainer
from unipaith.models.ml_loop import (
    DriftSnapshot,
    EvaluationRun,
    FairnessReport,
    OutcomeRecord,
    TrainingRun,
)
from unipaith.models.matching import ModelRegistry
from unipaith.models.user import User
from unipaith.schemas.ml_loop import (
    CreateExperimentRequest,
    CycleResultResponse,
    DriftSnapshotResponse,
    EvaluationRunResponse,
    ExperimentResultResponse,
    FairnessDialRequest,
    FairnessReportResponse,
    LearningKPIResponse,
    ModelListResponse,
    ModelVersionResponse,
    OutcomeStatsResponse,
    PromoteModelRequest,
    TriggerTrainingRequest,
    TrainingRunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/ml", tags=["ml-admin"])

# ======================================================================
# Cycle triggers
# ======================================================================


@router.post("/cycle/run", response_model=CycleResultResponse)
async def run_full_cycle(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Trigger the complete ML improvement cycle."""
    orchestrator = MLOrchestrator(db)
    return await orchestrator.run_full_cycle(triggered_by="manual")


@router.post("/cycle/evaluate")
async def run_evaluation(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Run model evaluation only."""
    orchestrator = MLOrchestrator(db)
    return await orchestrator.run_evaluation_only()


@router.post("/cycle/drift-check")
async def run_drift_check(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Run drift detection only."""
    orchestrator = MLOrchestrator(db)
    return await orchestrator.run_drift_check_only()


@router.post("/cycle/backfill-outcomes")
async def backfill(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Backfill outcome records from historical data."""
    orchestrator = MLOrchestrator(db)
    return await orchestrator.backfill_outcomes()


# ======================================================================
# Evaluations
# ======================================================================


@router.get("/evaluations", response_model=list[EvaluationRunResponse])
async def list_evaluations(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List recent evaluation runs."""
    stmt = (
        select(EvaluationRun)
        .order_by(EvaluationRun.started_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/evaluations/{eval_id}", response_model=EvaluationRunResponse)
async def get_evaluation(
    eval_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get a single evaluation run by ID."""
    from unipaith.core.exceptions import NotFoundException

    eval_run = await db.get(EvaluationRun, eval_id)
    if not eval_run:
        raise NotFoundException("Evaluation run not found")
    return eval_run


# ======================================================================
# Training
# ======================================================================


@router.get("/training", response_model=list[TrainingRunResponse])
async def list_training_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List recent training runs."""
    stmt = (
        select(TrainingRun)
        .order_by(TrainingRun.started_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/training/trigger", response_model=TrainingRunResponse)
async def trigger_training(
    body: TriggerTrainingRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Manually trigger a training run."""
    payload = body or TriggerTrainingRequest(
        triggered_by="manual",
        mode=settings.training_default_manual_mode,
    )
    trainer = ModelTrainer(db)
    return await trainer.run_training(
        triggered_by=payload.triggered_by,
        mode=payload.mode,
        trigger_reason=f"manual_trigger:{payload.mode}",
    )


# ======================================================================
# Model registry
# ======================================================================


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List all model versions."""
    manager = ModelManager(db)
    models_raw = await manager.list_models()
    active = await manager.get_active_model()
    models = [
        ModelVersionResponse.model_validate(m, from_attributes=True)
        for m in models_raw
    ]
    return ModelListResponse(
        models=models,
        active_version=active.model_version if active else None,
    )


@router.post("/models/promote")
async def promote_model(
    body: PromoteModelRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Promote a specific model version to active."""
    manager = ModelManager(db)
    return await manager.promote_model(
        model_version=body.model_version,
        force=body.force,
    )


@router.post("/models/rollback")
async def rollback_model(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Rollback to the previous active model version."""
    manager = ModelManager(db)
    return await manager.rollback_model()


# ======================================================================
# A/B tests
# ======================================================================


@router.post("/ab-tests")
async def create_ab_test(
    body: CreateExperimentRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create a new A/B test experiment."""
    manager = ABTestManager(db)
    return await manager.create_experiment(
        experiment_name=body.experiment_name,
        challenger_version=body.challenger_version,
        traffic_pct=body.traffic_pct,
    )


@router.get("/ab-tests/{experiment_name}", response_model=ExperimentResultResponse)
async def get_ab_test_results(
    experiment_name: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Evaluate and return results for an A/B test experiment."""
    manager = ABTestManager(db)
    return await manager.evaluate_experiment(experiment_name)


# ======================================================================
# Drift
# ======================================================================


@router.get("/drift", response_model=list[DriftSnapshotResponse])
async def list_drift(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List recent drift snapshots."""
    stmt = (
        select(DriftSnapshot)
        .order_by(DriftSnapshot.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# ======================================================================
# Fairness
# ======================================================================


@router.get("/fairness/{model_version}", response_model=list[FairnessReportResponse])
async def get_fairness(
    model_version: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get fairness reports for a specific model version."""
    stmt = select(FairnessReport).where(
        FairnessReport.model_version == model_version
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put("/fairness/dial")
async def update_fairness_dial(
    body: FairnessDialRequest,
    _admin: User = Depends(require_admin),
):
    """Update the in-memory fairness dial setting."""
    settings.fairness_dial = body.dial_value
    return {"fairness_dial": settings.fairness_dial}


# ======================================================================
# Outcomes
# ======================================================================


@router.get("/outcomes/stats", response_model=OutcomeStatsResponse)
async def outcome_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Return aggregate statistics on collected outcome records."""
    # Total count
    total_q = await db.execute(select(func.count(OutcomeRecord.id)))
    total = total_q.scalar() or 0

    # By source
    source_q = await db.execute(
        select(OutcomeRecord.outcome_source, func.count(OutcomeRecord.id)).group_by(
            OutcomeRecord.outcome_source
        )
    )
    by_source = {row[0] or "unknown": row[1] for row in source_q.all()}

    # By outcome
    outcome_q = await db.execute(
        select(OutcomeRecord.actual_outcome, func.count(OutcomeRecord.id)).group_by(
            OutcomeRecord.actual_outcome
        )
    )
    by_outcome = {row[0] or "unknown": row[1] for row in outcome_q.all()}

    # Date range
    range_q = await db.execute(
        select(
            func.min(OutcomeRecord.created_at),
            func.max(OutcomeRecord.created_at),
        )
    )
    row = range_q.one()
    earliest, latest = row[0], row[1]

    return OutcomeStatsResponse(
        total_outcomes=total,
        by_source=by_source,
        by_outcome=by_outcome,
        earliest=earliest,
        latest=latest,
    )


@router.get("/kpis", response_model=LearningKPIResponse)
async def learning_kpis(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Return backend-only KPI signals for learning speed and cycle quality."""
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    latest_outcome = await db.scalar(
        select(func.max(OutcomeRecord.outcome_recorded_at))
    )
    latest_eval = await db.scalar(select(func.max(EvaluationRun.started_at)))
    latest_training = await db.scalar(select(func.max(TrainingRun.started_at)))

    latest_eval_obj = await db.execute(
        select(EvaluationRun).order_by(EvaluationRun.started_at.desc()).limit(1)
    )
    eval_row = latest_eval_obj.scalar_one_or_none()
    training_after_eval = None
    if eval_row and eval_row.started_at:
        training_after_eval = await db.scalar(
            select(func.min(TrainingRun.started_at)).where(
                TrainingRun.started_at >= eval_row.started_at
            )
        )

    train_24h = await db.scalar(
        select(func.count()).select_from(TrainingRun).where(
            TrainingRun.started_at >= since_24h,
            TrainingRun.status == "completed",
        )
    )
    train_7d = await db.scalar(
        select(func.count()).select_from(TrainingRun).where(
            TrainingRun.started_at >= since_7d,
            TrainingRun.status == "completed",
        )
    )
    promos_7d = await db.scalar(
        select(func.count()).select_from(ModelRegistry).where(
            ModelRegistry.promoted_at >= since_7d
        )
    )
    rollbacks_7d = await db.scalar(
        select(func.count()).select_from(ModelRegistry).where(
            ModelRegistry.retired_at >= since_7d
        )
    )
    failed_train_7d = await db.scalar(
        select(func.count()).select_from(TrainingRun).where(
            TrainingRun.started_at >= since_7d,
            TrainingRun.status == "failed",
        )
    )
    total_train_7d = await db.scalar(
        select(func.count()).select_from(TrainingRun).where(
            TrainingRun.started_at >= since_7d
        )
    )

    active_model = await db.execute(
        select(ModelRegistry)
        .where(ModelRegistry.is_active.is_(True))
        .limit(1)
    )
    active_model_row = active_model.scalar_one_or_none()

    latest_completed_train = await db.execute(
        select(TrainingRun)
        .where(
            TrainingRun.status == "completed",
            TrainingRun.test_metrics.is_not(None),
        )
        .order_by(TrainingRun.started_at.desc())
        .limit(1)
    )
    latest_completed_train_row = latest_completed_train.scalar_one_or_none()

    net_uplift = None
    if active_model_row and latest_completed_train_row:
        active_acc = (active_model_row.performance_metrics or {}).get("accuracy")
        latest_acc = (latest_completed_train_row.test_metrics or {}).get("accuracy")
        if isinstance(active_acc, (int, float)) and isinstance(latest_acc, (int, float)):
            net_uplift = float(latest_acc) - float(active_acc)

    hours_outcome_to_eval = None
    if latest_outcome and latest_eval and latest_eval >= latest_outcome:
        hours_outcome_to_eval = round(
            (latest_eval - latest_outcome).total_seconds() / 3600, 3
        )

    hours_eval_to_training = None
    if eval_row and eval_row.started_at and training_after_eval:
        hours_eval_to_training = round(
            (training_after_eval - eval_row.started_at).total_seconds() / 3600, 3
        )

    fail_rate = None
    if total_train_7d:
        fail_rate = round((failed_train_7d or 0) / total_train_7d, 4)

    return LearningKPIResponse(
        generated_at=now,
        latest_outcome_at=latest_outcome,
        latest_evaluation_at=latest_eval,
        latest_training_at=latest_training,
        hours_outcome_to_eval_latest=hours_outcome_to_eval,
        hours_eval_to_training_latest=hours_eval_to_training,
        retrain_runs_24h=int(train_24h or 0),
        retrain_runs_7d=int(train_7d or 0),
        promotions_7d=int(promos_7d or 0),
        rollbacks_7d=int(rollbacks_7d or 0),
        training_failure_rate_7d=fail_rate,
        net_accuracy_uplift_vs_active=net_uplift,
    )
