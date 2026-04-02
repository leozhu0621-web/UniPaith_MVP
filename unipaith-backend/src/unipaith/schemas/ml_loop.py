"""Pydantic schemas for the ML self-improving loop admin API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Outcomes
# ---------------------------------------------------------------------------


class OutcomeStatsResponse(BaseModel):
    total_outcomes: int
    by_source: dict[str, int]
    by_outcome: dict[str, int]
    earliest: datetime | None = None
    latest: datetime | None = None


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    model_version: str | None = None
    evaluation_type: str | None = None
    dataset_size: int | None = None
    metrics: dict[str, Any] | None = None
    confusion_matrix: dict[str, Any] | None = None
    per_tier_metrics: dict[str, Any] | None = None
    fairness_metrics: dict[str, Any] | None = None
    drift_detected: bool | None = None
    drift_details: dict[str, Any] | None = None
    retraining_triggered: bool | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


class TrainingRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    triggered_by: str | None = None
    evaluation_run_id: Any | None = None
    training_data_size: int | None = None
    test_data_size: int | None = None
    feature_columns: list[str] | None = None
    algorithm: str | None = None
    mode: str | None = None
    trigger_reason: str | None = None
    new_outcomes_count: int | None = None
    data_window_start: datetime | None = None
    data_window_end: datetime | None = None
    hyperparameters: dict[str, Any] | None = None
    cv_metrics: dict[str, Any] | None = None
    test_metrics: dict[str, Any] | None = None
    fairness_metrics: dict[str, Any] | None = None
    fairness_passed: bool | None = None
    model_artifact_path: str | None = None
    resulting_model_version: str | None = None
    status: str | None = None
    failure_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    model_version: str | None = None
    architecture: str | None = None
    hyperparameters: dict[str, Any] | None = None
    performance_metrics: dict[str, Any] | None = None
    is_active: bool | None = None
    trained_at: datetime | None = None
    promoted_at: datetime | None = None
    retired_at: datetime | None = None
    created_at: datetime | None = None


class ModelListResponse(BaseModel):
    models: list[ModelVersionResponse]
    active_version: str | None = None


class PromoteModelRequest(BaseModel):
    model_version: str
    force: bool = False


class TriggerTrainingRequest(BaseModel):
    triggered_by: str = "manual"
    mode: Literal["fast", "full"] = "full"


# ---------------------------------------------------------------------------
# A/B testing
# ---------------------------------------------------------------------------


class CreateExperimentRequest(BaseModel):
    experiment_name: str
    challenger_version: str
    traffic_pct: float | None = None


class ExperimentResultResponse(BaseModel):
    status: str
    control: dict[str, Any] | None = None
    challenger: dict[str, Any] | None = None
    lift: float | None = None
    recommendation: str | None = None


# ---------------------------------------------------------------------------
# Drift
# ---------------------------------------------------------------------------


class DriftSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    snapshot_type: str | None = None
    reference_period_start: datetime | None = None
    reference_period_end: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    feature_name: str | None = None
    reference_stats: dict[str, Any] | None = None
    current_stats: dict[str, Any] | None = None
    test_statistic: float | None = None
    p_value: float | None = None
    drift_detected: bool | None = None
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Fairness
# ---------------------------------------------------------------------------


class FairnessReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    model_version: str | None = None
    evaluation_run_id: Any | None = None
    training_run_id: Any | None = None
    protected_attribute: str | None = None
    group_metrics: dict[str, Any] | None = None
    demographic_parity_diff: float | None = None
    equal_opportunity_diff: float | None = None
    equalized_odds_diff: float | None = None
    fairness_dial_setting: float | None = None
    passed: bool | None = None
    violation_details: dict[str, Any] | None = None
    created_at: datetime | None = None


class FairnessDialRequest(BaseModel):
    dial_value: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Full cycle
# ---------------------------------------------------------------------------


class CycleResultResponse(BaseModel):
    started_at: datetime | None = None
    completed_at: datetime | None = None
    decision: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None
    drift: dict[str, Any] | None = None
    training: dict[str, Any] | None = None
    fairness: dict[str, Any] | None = None
    promotion: dict[str, Any] | None = None


class LearningKPIResponse(BaseModel):
    generated_at: datetime
    latest_outcome_at: datetime | None = None
    latest_evaluation_at: datetime | None = None
    latest_training_at: datetime | None = None
    hours_outcome_to_eval_latest: float | None = None
    hours_eval_to_training_latest: float | None = None
    retrain_runs_24h: int
    retrain_runs_7d: int
    promotions_7d: int
    rollbacks_7d: int
    promotion_hit_rate_7d: float | None = None
    training_failure_rate_7d: float | None = None
    net_accuracy_uplift_vs_active: float | None = None
    avg_evaluation_duration_ms_7d: float | None = None
    avg_training_duration_ms_7d: float | None = None
    runtime_provider: str | None = None
    runtime_mode: str | None = None


class CycleHealthResponse(BaseModel):
    generated_at: datetime
    scheduler_effective_enabled: bool
    latest_evaluation: dict[str, Any] | None = None
    latest_training: dict[str, Any] | None = None
    latest_drift: dict[str, Any] | None = None
    latest_cycle_decision: dict[str, Any] | None = None
    blocking_reasons: list[str]
    readiness_score: float


class TrendPoint(BaseModel):
    date: str
    value: float


class LearningTrendsResponse(BaseModel):
    generated_at: datetime
    evals_per_day: list[TrendPoint]
    completed_trains_per_day: list[TrendPoint]
    failed_trains_per_day: list[TrendPoint]
    avg_hours_eval_to_train_per_day: list[TrendPoint]
    avg_hours_outcome_to_eval_per_day: list[TrendPoint]


class SchedulerSmokeResponse(BaseModel):
    generated_at: datetime
    scheduler_effective_enabled: bool
    scheduler_running: bool
    expected_job_ids: list[str]
    registered_job_ids: list[str]
    missing_job_ids: list[str]
    next_run_times: dict[str, str | None]


class ArchitectureStageStatus(BaseModel):
    stage_id: str
    label: str
    status: Literal["ok", "warning", "error", "idle"]
    last_run_at: datetime | None = None
    duration_ms: float | None = None
    counts: dict[str, int | float | str | None] = Field(default_factory=dict)
    error: str | None = None
    source: str


class ArchitectureRunTrace(BaseModel):
    run_id: str
    run_type: Literal["engine", "training", "evaluation", "crawler", "promotion", "outcome"]
    status: Literal["ok", "warning", "error", "idle", "degraded"]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    stage_id: str
    mode: str | None = None
    trigger_reason: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    links: dict[str, str] = Field(default_factory=dict)


class ArchitectureTraceResponse(BaseModel):
    generated_at: datetime
    stages: list[ArchitectureStageStatus]
    runs: list[ArchitectureRunTrace]
