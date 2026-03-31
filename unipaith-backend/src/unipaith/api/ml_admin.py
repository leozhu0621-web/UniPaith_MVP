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
from unipaith.models.user import User
from unipaith.schemas.ml_loop import (
    CreateExperimentRequest,
    CycleResultResponse,
    DriftSnapshotResponse,
    EvaluationRunResponse,
    ExperimentResultResponse,
    FairnessDialRequest,
    FairnessReportResponse,
    ModelListResponse,
    ModelVersionResponse,
    OutcomeStatsResponse,
    PromoteModelRequest,
    TrainingRunResponse,
    TriggerTrainingRequest,
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
    stmt = select(EvaluationRun).order_by(EvaluationRun.started_at.desc()).limit(limit)
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
    stmt = select(TrainingRun).order_by(TrainingRun.started_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/training/trigger", response_model=TrainingRunResponse)
async def trigger_training(
    body: TriggerTrainingRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Manually trigger a training run."""
    trainer = ModelTrainer(db)
    return await trainer.run_training(triggered_by=body.triggered_by)


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
    models = [ModelVersionResponse.model_validate(m, from_attributes=True) for m in models_raw]
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
    stmt = select(DriftSnapshot).order_by(DriftSnapshot.created_at.desc()).limit(limit)
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
    stmt = select(FairnessReport).where(FairnessReport.model_version == model_version)
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
