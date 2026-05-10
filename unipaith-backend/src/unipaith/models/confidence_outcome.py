"""Phase D2 — confidence-outcome pairs (D2 calibrator's training data).

One row per (student, program) pair when an event fires that reflects
on the matcher's confidence prediction:

  - applied      : the student submitted an application for this program
  - accepted     : the institution accepted that application
  - enrolled     : the student enrolled
  - aged_out     : a backfill job stamped outcome=0 for a recommendation
                   that aged out without an application (negative example)

The calibrator (`unipaith.services.confidence_calibrator.fit_calibrator`)
consumes `(predicted_confidence, outcome)` tuples from this table to fit
the isotonic regression. Cold start: no rows → calibrator stays
unfitted → matcher's raw confidence flows through.

Why a dedicated table
---------------------
- The existing `outcome_records` table (`unipaith.models.ml_loop`) stores
  fitness-score predictions for the legacy ML loop. Confidence
  calibration has different semantics: a *binary* outcome compared to
  a *probability* prediction, with the calibrator fit as a
  monotone-increasing piecewise-linear function. Conflating these
  would force a bunch of NULL/optional fields.
- D2's input pairs are append-only and indexed for the windowed-read
  pattern the fit job uses. The existing outcome table is keyed off
  prediction_log, which doesn't exist on the Plan 2 surface.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, UUIDPrimaryKeyMixin


class ConfidenceOutcomePair(Base, UUIDPrimaryKeyMixin):
    """A single (predicted_confidence, outcome) data point for D2.

    Insertion path: `unipaith.services.confidence_outcome_service.
    record_outcome()` — called from the application / offer-response /
    enrollment event hooks. The service looks up
    `MatchResult.confidence_score` at event time and stamps it onto
    `predicted_confidence`, so even after re-emit (which would change
    the live confidence) the historical pair stays anchored to the
    prediction the student actually saw.
    """

    __tablename__ = "confidence_outcome_pairs"
    __table_args__ = (
        CheckConstraint("outcome IN (0, 1)", name="ck_cop_outcome_binary"),
        CheckConstraint(
            "outcome_kind IN ('applied', 'accepted', 'enrolled', 'aged_out')",
            name="ck_cop_outcome_kind",
        ),
        Index("ix_cop_kind_created", "outcome_kind", "created_at"),
        Index("ix_cop_student", "student_id"),
        Index("ix_cop_program", "program_id"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    predicted_confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False
    )
    outcome: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    outcome_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
