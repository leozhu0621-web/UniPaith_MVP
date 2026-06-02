"""Spec 46 §6 — Fairness governance: disparate-impact signals + auto-halt overrides.

Two tables back the contractual auto-halt commitment (Landing_MVP, verbatim):

    "If disparate-impact Δ exceeds 0.20 for two consecutive weeks, the model stops
     scoring new applicants for that cohort."

``FairnessSignal`` is the weekly disparate-impact record per (program × week ×
protected attribute). ``FairnessOverride`` records an institution admin's
audit-logged decision to resume scoring after a halt. The halt *state* itself
lives on ``programs`` (``matching_halted`` / ``fairness_override_active`` /
``fairness_override_expires_at`` / ``fairness_threshold``) so the match service
can gate on a single row read — see ``models/institution.Program``.

This is deterministic statistics; no LLM agent is involved (the
``ck_ai_turns_agent`` vocabulary is untouched).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base

# Spec 46 §6.1 — protected attributes tracked. race/disability are listed for
# completeness but are only computed where the institution collects them.
PROTECTED_ATTRIBUTES = (
    "race",
    "gender",
    "first_gen",
    "international",
    "nationality_region",
    "disability",
    "veteran",
)
_ATTR_CHECK_SQL = (
    "protected_attribute IN (" + ",".join(f"'{a}'" for a in PROTECTED_ATTRIBUTES) + ")"
)

# Spec 46 §6.5 — severity ladder. `info` = within threshold (or insufficient
# sample); `warning` = approaching; `high` = Δ over threshold this week;
# `auto_halt` = second consecutive breach (scoring stopped); `override_active`
# = an admin resumed scoring.
FAIRNESS_SEVERITIES = ("info", "warning", "high", "auto_halt", "override_active")
_SEVERITY_CHECK_SQL = "severity IN (" + ",".join(f"'{s}'" for s in FAIRNESS_SEVERITIES) + ")"


class FairnessSignal(Base):
    """A weekly disparate-impact reading for one (program, week, attribute)."""

    __tablename__ = "fairness_signals"
    __table_args__ = (
        # One reading per cohort-week-attribute; recompute upserts on this key.
        UniqueConstraint(
            "program_id",
            "week_start",
            "protected_attribute",
            name="uq_fairness_signals_cohort_week_attr",
        ),
        CheckConstraint(_ATTR_CHECK_SQL, name="ck_fairness_signals_attribute"),
        CheckConstraint(_SEVERITY_CHECK_SQL, name="ck_fairness_signals_severity"),
        Index("ix_fairness_signals_program_week", "program_id", "week_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Cohort = intake_round × program (§6.1). Nullable: the weekly compute keys
    # on (program, week) and back-fills the round when one is resolvable.
    intake_round_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intake_rounds.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Monday (UTC) that starts the measured week.
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    protected_attribute: Mapped[str] = mapped_column(Text, nullable=False)
    cohort_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # DI = P(positive | minority) / P(positive | majority). NULL when the
    # sample is below the §6.1 floor (50) — flagged, never scored fair/unfair.
    di_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    # Δ = |1 - DI|. NULL alongside di_ratio when sample insufficient.
    delta: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    severity: Mapped[str] = mapped_column(Text, nullable=False, default="info")
    sample_sufficient: Mapped[bool] = mapped_column(default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    # Dashboard detail (minority/majority labels + positive rates + counts).
    # Shape: {minority_label, majority_label, minority_rate, majority_rate,
    #         minority_n, majority_n, threshold}. Kept off the typed columns so
    #         §6.5's schema stays minimal.
    detail: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FairnessOverride(Base):
    """An institution admin's audit-logged decision to resume scoring (§6.3)."""

    __tablename__ = "fairness_overrides"
    __table_args__ = (Index("ix_fairness_overrides_program_active", "program_id", "revoked_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The signal that triggered the halt this override clears. SET NULL so
    # pruning old signals doesn't drop the override audit trail.
    fairness_signal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fairness_signals.id", ondelete="SET NULL"),
        nullable=True,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # §6.3 — written rationale, enforced ≥100 chars at the service layer.
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    override_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
