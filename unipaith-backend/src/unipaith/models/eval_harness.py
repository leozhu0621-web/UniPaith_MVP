"""Spec 62 §8 — the two persisted additions for the shared eval harness.

The harness *reuses* the ``ml_loop`` tables (``evaluation_runs``,
``ab_test_assignments``, ``drift_snapshots``, ``fairness_reports``) and the
``ai_turns`` / ``ai_turn_feedback`` ledger; it adds exactly two tables:

- ``eval_cases``   — the versioned golden set: one row per curated/production/
  synthetic case, per consumer, per rubric version. Grows from real failures
  (the adapter's ``materialize`` hook), so nothing re-breaks (§2).
- ``eval_results`` — one row per case, per run: the per-dimension scores a run
  produced, joined to its ``evaluation_runs`` row.

Public-data-safe: an ``eval_cases`` row is a curated test input + expected
output (a sample chatbot prompt, a labeled reference page) — never a real student
record. The chatbot golden cases are synthetic personas; the extraction cases are
public reference pages.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EvalCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A versioned golden-set case (§2/§8). Dedup key = (consumer, case_key,
    rubric_version) — re-running a fixture upserts rather than duplicates."""

    __tablename__ = "eval_cases"
    __table_args__ = (
        UniqueConstraint(
            "consumer", "case_key", "rubric_version", name="uq_eval_cases_consumer_key_version"
        ),
        Index("ix_eval_cases_consumer", "consumer"),
        Index("ix_eval_cases_source", "source"),
    )

    consumer: Mapped[str] = mapped_column(String(30), nullable=False)
    case_key: Mapped[str] = mapped_column(String(120), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(60))
    input_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    expected: Mapped[dict | None] = mapped_column(JSONB)
    dimensions: Mapped[list | None] = mapped_column(JSONB)
    rubric_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    # curated | production | synthetic (§2)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="curated")
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")


class EvalResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One case's verdict within one run (§8). Joined to the ``evaluation_runs``
    row the harness persisted for the gate."""

    __tablename__ = "eval_results"
    __table_args__ = (
        Index("ix_eval_results_run", "evaluation_run_id"),
        Index("ix_eval_results_case", "eval_case_id"),
        Index("ix_eval_results_consumer", "consumer"),
    )

    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    eval_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("eval_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    consumer: Mapped[str] = mapped_column(String(30), nullable=False)
    dimension_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    deterministic_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    judge_model: Mapped[str | None] = mapped_column(String(50))
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False, default=Decimal("0"))
