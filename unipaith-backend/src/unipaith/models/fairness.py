"""Spec 46 §6 — Fairness auto-halt governance.

The contractual commitment (verbatim from Landing_MVP, §6):

    "If disparate-impact Δ exceeds 0.20 for two consecutive weeks, the model
     stops scoring new applicants for that cohort."

Two tables back the mechanism:

- ``FairnessSignal`` — one row per (program × intake_round × protected_attribute
  × week). Records the disparate-impact ratio, Δ, cohort size, whether the
  sample is large enough to be meaningful (§6.1 — 50 scored applicants), and a
  severity escalation ladder (info → warning → high → auto_halt → override_active).
- ``FairnessOverride`` — an institution admin's logged decision to lift a halt,
  with a written rationale (≥100 chars per §6.3) and an expiry window.

The actual halt flag lives on ``programs.matching_halted`` (§6.2 "set
``programs.matching_halted = true``"); these tables are the evidence trail and
the audit surface behind it. Distinct from ``ml_loop.FairnessReport`` which
assesses a model *version* during training/eval — this is the per-cohort,
per-week production governance ledger.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base

# §6.1 protected attributes tracked. race/disability/veteran are emitted only
# when the institution collects them and the sample is large enough; otherwise
# the signal is recorded with sample_sufficient=False ("insufficient sample",
# never "fair/unfair").
PROTECTED_ATTRIBUTES = (
    "race",
    "gender",
    "first_gen",
    "international",
    "nationality_region",
    "disability",
    "veteran",
)
_ATTR_CHECK = "protected_attribute IN (" + ",".join(f"'{a}'" for a in PROTECTED_ATTRIBUTES) + ")"

# §6.2 / §6.5 severity ladder.
FAIRNESS_SEVERITIES = ("info", "warning", "high", "auto_halt", "override_active")
_SEVERITY_CHECK = "severity IN (" + ",".join(f"'{s}'" for s in FAIRNESS_SEVERITIES) + ")"


class FairnessSignal(Base):
    """§6.5 — a single weekly disparate-impact reading for one cohort×attribute."""

    __tablename__ = "fairness_signals"
    __table_args__ = (
        # Idempotent recompute key — the service upserts on this tuple. A
        # plain (non-unique) index keeps the lookup fast; the service enforces
        # one-row-per-key (NULL intake_round_id is handled in Python since
        # Postgres treats NULLs as distinct in a UNIQUE constraint).
        Index(
            "ix_fairness_signals_cohort_week",
            "program_id",
            "intake_round_id",
            "protected_attribute",
            "week_start",
        ),
        Index("ix_fairness_signals_program_week", "program_id", "week_start"),
        CheckConstraint(_ATTR_CHECK, name="ck_fairness_signals_attribute"),
        CheckConstraint(_SEVERITY_CHECK, name="ck_fairness_signals_severity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The MVP does not tie applications/match_results to a specific intake round,
    # so this is the program's active intake when one exists, else NULL. Cohort
    # is keyed on (program × week) with the intake recorded for context.
    intake_round_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intake_rounds.id", ondelete="SET NULL"),
        nullable=True,
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    protected_attribute: Mapped[str] = mapped_column(String(30), nullable=False)
    cohort_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # DI = P(positive | minority) / P(positive | majority). Null when there is
    # no comparison group (single-group or zero-sample cohort).
    di_ratio: Mapped[float | None] = mapped_column(Numeric(6, 4))
    # Δ = |1 - DI|.
    delta: Mapped[float | None] = mapped_column(Numeric(6, 4))
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    sample_sufficient: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    overrides: Mapped[list[FairnessOverride]] = relationship(
        back_populates="signal", cascade="all, delete-orphan"
    )


class FairnessOverride(Base):
    """§6.3 — an institution admin's logged decision to lift a halt."""

    __tablename__ = "fairness_overrides"
    __table_args__ = (Index("ix_fairness_overrides_signal", "fairness_signal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fairness_signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fairness_signals.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The admin who approved the override (audit actor). SET NULL so deleting a
    # user never erases the override record itself.
    institution_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    override_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    signal: Mapped[FairnessSignal] = relationship(back_populates="overrides")
