"""Phase A — Student goals model (SMART goal stack).

One row per goal. Discovery-sourced goals carry source_session_id for
provenance; manual goals must NOT carry one (enforced by CHECK constraint and
by GoalsService).
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
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class StudentGoal(Base):
    __tablename__ = "student_goals"
    __table_args__ = (
        CheckConstraint(
            "category IN ('academic','social','personal')",
            name="ck_student_goals_category",
        ),
        CheckConstraint(
            "status IN ('active','met','revised','dropped')",
            name="ck_student_goals_status",
        ),
        CheckConstraint(
            "source IN ('discovery','manual')",
            name="ck_student_goals_source",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_student_goals_confidence",
        ),
        CheckConstraint(
            "(source = 'discovery' AND source_session_id IS NOT NULL)"
            " OR (source = 'manual' AND source_session_id IS NULL)",
            name="ck_student_goals_source_provenance",
        ),
        Index("ix_student_goals_student_status", "student_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    specific: Mapped[str] = mapped_column(Text, nullable=False)
    measurable: Mapped[str | None] = mapped_column(Text)
    achievable_notes: Mapped[str | None] = mapped_column(Text)
    relevant_notes: Mapped[str | None] = mapped_column(Text)
    time_bound: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    source_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
