"""Pydantic schemas for the ML self-improving loop admin API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

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
    evaluation: dict[str, Any] | None = None
    drift: dict[str, Any] | None = None
    training: dict[str, Any] | None = None
    fairness: dict[str, Any] | None = None
    promotion: dict[str, Any] | None = None
