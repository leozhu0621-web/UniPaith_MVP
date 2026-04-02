"""
Phase 4: Self-Improving Loop models.
Tracks outcomes, evaluations, training runs, A/B tests, drift, and fairness.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base


class OutcomeRecord(Base):
    """Links a prediction to its actual ground-truth outcome."""

    __tablename__ = "outcome_records"
    __table_args__ = (
        Index("ix_outcome_records_student", "student_id"),
        Index("ix_outcome_records_program", "program_id"),
        Index("ix_outcome_records_outcome", "actual_outcome"),
        Index("ix_outcome_records_recorded_at", "outcome_recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prediction_logs.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    predicted_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    predicted_tier: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    outcome_source: Mapped[str] = mapped_column(String(30), nullable=False)
    outcome_confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    features_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    outcome_recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvaluationRun(Base):
    """Person B evaluation: compares predictions vs actual outcomes."""

    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_evaluation_runs_model", "model_version"),
        Index("ix_evaluation_runs_started", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    evaluation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    dataset_size: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confusion_matrix: Mapped[dict | None] = mapped_column(JSONB)
    per_tier_metrics: Mapped[dict | None] = mapped_column(JSONB)
    fairness_metrics: Mapped[dict | None] = mapped_column(JSONB)
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    drift_details: Mapped[dict | None] = mapped_column(JSONB)
    retraining_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    training_runs: Mapped[list[TrainingRun]] = relationship(back_populates="evaluation_run")
    fairness_reports: Mapped[list[FairnessReport]] = relationship(
        back_populates="evaluation_run",
        foreign_keys="[FairnessReport.evaluation_run_id]",
    )


class TrainingRun(Base):
    """Person C training: AutoML retraining on accumulated labeled data."""

    __tablename__ = "training_runs"
    __table_args__ = (
        Index("ix_training_runs_status", "status"),
        Index("ix_training_runs_started", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    triggered_by: Mapped[str] = mapped_column(String(30), nullable=False)
    evaluation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="SET NULL")
    )
    training_data_size: Mapped[int] = mapped_column(Integer, nullable=False)
    test_data_size: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_columns: Mapped[dict] = mapped_column(JSONB, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="full")
    trigger_reason: Mapped[str | None] = mapped_column(String(120))
    new_outcomes_count: Mapped[int | None] = mapped_column(Integer)
    data_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hyperparameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    optuna_study_name: Mapped[str | None] = mapped_column(String(100))
    cv_metrics: Mapped[dict | None] = mapped_column(JSONB)
    test_metrics: Mapped[dict | None] = mapped_column(JSONB)
    fairness_metrics: Mapped[dict | None] = mapped_column(JSONB)
    fairness_passed: Mapped[bool | None] = mapped_column(Boolean)
    model_artifact_path: Mapped[str | None] = mapped_column(String(500))
    resulting_model_version: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evaluation_run: Mapped[EvaluationRun | None] = relationship(back_populates="training_runs")
    fairness_reports: Mapped[list[FairnessReport]] = relationship(
        back_populates="training_run",
        foreign_keys="[FairnessReport.training_run_id]",
    )


class ABTestAssignment(Base):
    """Sticky A/B test variant assignment for a student."""

    __tablename__ = "ab_test_assignments"
    __table_args__ = (
        Index("ix_ab_test_student_experiment", "student_id", "experiment_name", unique=True),
        Index("ix_ab_test_experiment", "experiment_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    experiment_name: Mapped[str] = mapped_column(String(100), nullable=False)
    variant: Mapped[str] = mapped_column(String(20), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    outcome_recorded: Mapped[bool] = mapped_column(Boolean, default=False)


class DriftSnapshot(Base):
    """Statistical snapshot for drift detection via KS test."""

    __tablename__ = "drift_snapshots"
    __table_args__ = (
        Index("ix_drift_snapshots_type", "snapshot_type"),
        Index("ix_drift_snapshots_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    reference_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    feature_name: Mapped[str | None] = mapped_column(String(100))
    reference_stats: Mapped[dict] = mapped_column(JSONB, nullable=False)
    current_stats: Mapped[dict] = mapped_column(JSONB, nullable=False)
    test_statistic: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    p_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 8))
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FairnessReport(Base):
    """Fairness assessment for a model version across a protected attribute."""

    __tablename__ = "fairness_reports"
    __table_args__ = (
        Index("ix_fairness_reports_model", "model_version"),
        Index("ix_fairness_reports_attribute", "protected_attribute"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    evaluation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="SET NULL")
    )
    training_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_runs.id", ondelete="SET NULL")
    )
    protected_attribute: Mapped[str] = mapped_column(String(50), nullable=False)
    group_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    demographic_parity_diff: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    equal_opportunity_diff: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    equalized_odds_diff: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    fairness_dial_setting: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    violation_details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evaluation_run: Mapped[EvaluationRun | None] = relationship(
        back_populates="fairness_reports",
        foreign_keys=[evaluation_run_id],
    )
    training_run: Mapped[TrainingRun | None] = relationship(
        back_populates="fairness_reports",
        foreign_keys=[training_run_id],
    )
