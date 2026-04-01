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
    CycleHealthResponse,
    CreateExperimentRequest,
    CycleResultResponse,
    DriftSnapshotResponse,
    EvaluationRunResponse,
    ExperimentResultResponse,
    FairnessDialRequest,
    FairnessReportResponse,
    LearningTrendsResponse,
    LearningKPIResponse,
    ModelListResponse,
    ModelVersionResponse,
    OutcomeStatsResponse,
    PromoteModelRequest,
    TriggerTrainingRequest,
    TrainingRunResponse,
    TrendPoint,
    SchedulerSmokeResponse,
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


@router.get("/cycle/health", response_model=CycleHealthResponse)
async def cycle_health(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Single-shot health for the backend ML learning loop."""
    now = datetime.now(timezone.utc)
    scheduler_effective_enabled = settings.scheduler_enabled or (
        settings.scheduler_auto_enable_non_test and settings.environment != "test"
    )

    latest_eval_row = await db.execute(
        select(EvaluationRun).order_by(EvaluationRun.started_at.desc()).limit(1)
    )
    latest_eval = latest_eval_row.scalar_one_or_none()

    latest_train_row = await db.execute(
        select(TrainingRun).order_by(TrainingRun.started_at.desc()).limit(1)
    )
    latest_train = latest_train_row.scalar_one_or_none()

    latest_drift_row = await db.execute(
        select(DriftSnapshot).order_by(DriftSnapshot.created_at.desc()).limit(1)
    )
    latest_drift = latest_drift_row.scalar_one_or_none()

    outcomes_total = int(
        (
            await db.execute(
                select(func.count()).select_from(OutcomeRecord)
            )
        ).scalar()
        or 0
    )
    failed_train_7d = int(
        (
            await db.execute(
                select(func.count()).select_from(TrainingRun).where(
                    TrainingRun.started_at >= (now - timedelta(days=7)),
                    TrainingRun.status == "failed",
                )
            )
        ).scalar()
        or 0
    )

    blocking_reasons: list[str] = []
    if not scheduler_effective_enabled:
        blocking_reasons.append("scheduler_disabled")
    if outcomes_total < settings.outcome_min_decisions_for_training:
        blocking_reasons.append("insufficient_outcomes_for_training")
    if latest_train and latest_train.status == "failed":
        blocking_reasons.append("latest_training_failed")
    if failed_train_7d >= 3:
        blocking_reasons.append("high_training_failure_rate_7d")
    if latest_drift and latest_drift.drift_detected:
        blocking_reasons.append("drift_detected")

    readiness_score = 1.0
    if blocking_reasons:
        readiness_score = max(0.0, 1.0 - min(0.9, 0.15 * len(blocking_reasons)))

    latest_cycle_decision = None
    if latest_train:
        latest_cycle_decision = {
            "mode": latest_train.mode,
            "trigger_reason": latest_train.trigger_reason,
            "new_outcomes_count": latest_train.new_outcomes_count,
            "status": latest_train.status,
            "failure_reason": latest_train.failure_reason,
            "started_at": latest_train.started_at.isoformat() if latest_train.started_at else None,
        }

    return CycleHealthResponse(
        generated_at=now,
        scheduler_effective_enabled=scheduler_effective_enabled,
        latest_evaluation=(
            {
                "id": str(latest_eval.id),
                "model_version": latest_eval.model_version,
                "dataset_size": latest_eval.dataset_size,
                "retraining_triggered": latest_eval.retraining_triggered,
                "started_at": latest_eval.started_at.isoformat() if latest_eval.started_at else None,
            }
            if latest_eval
            else None
        ),
        latest_training=(
            {
                "id": str(latest_train.id),
                "status": latest_train.status,
                "mode": latest_train.mode,
                "resulting_model_version": latest_train.resulting_model_version,
                "started_at": latest_train.started_at.isoformat() if latest_train.started_at else None,
            }
            if latest_train
            else None
        ),
        latest_drift=(
            {
                "id": str(latest_drift.id),
                "drift_detected": latest_drift.drift_detected,
                "feature_name": latest_drift.feature_name,
                "created_at": latest_drift.created_at.isoformat() if latest_drift.created_at else None,
            }
            if latest_drift
            else None
        ),
        latest_cycle_decision=latest_cycle_decision,
        blocking_reasons=blocking_reasons,
        readiness_score=round(readiness_score, 3),
    )


@router.get("/trends", response_model=LearningTrendsResponse)
async def learning_trends(
    days: int = Query(default=7, ge=3, le=30),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Time-series signals for ML learning speed and cycle throughput."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    eval_rows = (
        await db.execute(
            select(EvaluationRun).where(EvaluationRun.started_at >= since)
        )
    ).scalars().all()
    train_rows = (
        await db.execute(
            select(TrainingRun).where(TrainingRun.started_at >= since)
        )
    ).scalars().all()
    outcome_rows = (
        await db.execute(
            select(OutcomeRecord).where(OutcomeRecord.outcome_recorded_at >= since)
        )
    ).scalars().all()

    timeline_days: list[str] = [
        (now - timedelta(days=offset)).date().isoformat()
        for offset in reversed(range(days))
    ]
    eval_count = {d: 0 for d in timeline_days}
    train_ok_count = {d: 0 for d in timeline_days}
    train_fail_count = {d: 0 for d in timeline_days}
    eval_to_train_hours: dict[str, list[float]] = {d: [] for d in timeline_days}
    outcome_to_eval_hours: dict[str, list[float]] = {d: [] for d in timeline_days}

    outcomes_by_day: dict[str, list[datetime]] = {d: [] for d in timeline_days}
    for o in outcome_rows:
        day = o.outcome_recorded_at.date().isoformat()
        if day in outcomes_by_day:
            outcomes_by_day[day].append(o.outcome_recorded_at)

    eval_lookup: list[datetime] = []
    for e in eval_rows:
        day = e.started_at.date().isoformat()
        if day in eval_count:
            eval_count[day] += 1
            eval_lookup.append(e.started_at)
            same_day_outcomes = outcomes_by_day.get(day, [])
            if same_day_outcomes:
                latest_outcome = max(same_day_outcomes)
                if e.started_at >= latest_outcome:
                    outcome_to_eval_hours[day].append(
                        (e.started_at - latest_outcome).total_seconds() / 3600
                    )
    eval_lookup.sort()

    for t in train_rows:
        day = t.started_at.date().isoformat()
        if t.status == "completed" and day in train_ok_count:
            train_ok_count[day] += 1
        elif t.status == "failed" and day in train_fail_count:
            train_fail_count[day] += 1
        if day in eval_to_train_hours and eval_lookup:
            prior_eval = None
            for e_start in reversed(eval_lookup):
                if e_start <= t.started_at:
                    prior_eval = e_start
                    break
            if prior_eval is not None:
                eval_to_train_hours[day].append(
                    (t.started_at - prior_eval).total_seconds() / 3600
                )

    def _avg(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 3)

    return LearningTrendsResponse(
        generated_at=now,
        evals_per_day=[TrendPoint(date=d, value=float(eval_count[d])) for d in timeline_days],
        completed_trains_per_day=[TrendPoint(date=d, value=float(train_ok_count[d])) for d in timeline_days],
        failed_trains_per_day=[TrendPoint(date=d, value=float(train_fail_count[d])) for d in timeline_days],
        avg_hours_eval_to_train_per_day=[
            TrendPoint(date=d, value=_avg(eval_to_train_hours[d])) for d in timeline_days
        ],
        avg_hours_outcome_to_eval_per_day=[
            TrendPoint(date=d, value=_avg(outcome_to_eval_hours[d])) for d in timeline_days
        ],
    )


@router.get("/scheduler/smoke", response_model=SchedulerSmokeResponse)
async def scheduler_smoke(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Quick scheduler wiring/health check for production operations."""
    del db  # endpoint does not require database IO
    from unipaith.core.scheduler import scheduler

    now = datetime.now(timezone.utc)
    scheduler_effective_enabled = settings.scheduler_enabled or (
        settings.scheduler_auto_enable_non_test and settings.environment != "test"
    )
    expected_job_ids = ["ml_evaluation", "ml_training", "feature_refresh", "crawler_weekly"]
    if settings.gpu_mode == "aws":
        expected_job_ids.append("gpu_idle_check")
    if settings.scheduler_self_driving_enabled:
        expected_job_ids.append("ai_self_driving")

    jobs = scheduler.get_jobs() if scheduler.running else []
    registered = [job.id for job in jobs]
    missing = [job_id for job_id in expected_job_ids if job_id not in registered]
    next_run_times = {
        job.id: (job.next_run_time.isoformat() if job.next_run_time else None)
        for job in jobs
    }

    return SchedulerSmokeResponse(
        generated_at=now,
        scheduler_effective_enabled=scheduler_effective_enabled,
        scheduler_running=scheduler.running,
        expected_job_ids=expected_job_ids,
        registered_job_ids=registered,
        missing_job_ids=missing,
        next_run_times=next_run_times,
    )
