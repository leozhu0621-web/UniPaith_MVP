"""Fairness signals — per-program × protected-attribute × week disparate-impact.

Gap audit G-I5 / Spec 43 §6. The matching model must not silently disadvantage
a protected group. Each week the FairnessService computes the disparate-impact
ratio (4/5ths rule) of recommendation/selection rates between the reference
group and the most-disadvantaged group for each protected attribute. When the
disparate-impact DELTA (1 − ratio) exceeds the threshold (default 0.20) for two
consecutive weeks, the program's matching is auto-halted until a human admin
overrides (audit-logged).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base

# Protected attributes tracked for disparate-impact (Master Paper / Spec 43).
PROTECTED_ATTRIBUTES = ("gender_identity", "nationality", "first_generation_status")

# Default 4/5ths-rule delta: ratio < 0.80 (i.e. delta > 0.20) is adverse impact.
DEFAULT_DISPARATE_IMPACT_THRESHOLD = 0.20


class FairnessSignal(Base):
    __tablename__ = "fairness_signals"
    __table_args__ = (
        UniqueConstraint(
            "program_id",
            "protected_attribute",
            "week_start",
            name="uq_fairness_program_attr_week",
        ),
        Index("ix_fairness_program_week", "program_id", "week_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    protected_attribute: Mapped[str] = mapped_column(String(40), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)

    reference_group: Mapped[str | None] = mapped_column(String(120))
    disadvantaged_group: Mapped[str | None] = mapped_column(String(120))
    reference_rate: Mapped[float | None] = mapped_column(Float)
    disadvantaged_rate: Mapped[float | None] = mapped_column(Float)
    disparate_impact_ratio: Mapped[float | None] = mapped_column(Float)
    # 1 − ratio. Breach when > threshold.
    disparate_impact_delta: Mapped[float | None] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
