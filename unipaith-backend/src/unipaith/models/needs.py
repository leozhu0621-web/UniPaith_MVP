"""Phase A — Student needs model (Maslow-keyed needs map).

One row per need. Severity is required because the whole point of needs
classification is prioritization. Source 'inferred' allows session_id to be
present or null (the LLM may infer from cross-session signals).
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
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class StudentNeed(Base):
    __tablename__ = "student_needs"
    __table_args__ = (
        CheckConstraint(
            "maslow_level IN ('physiological','safety','social',"
            "'self_esteem','self_actualization')",
            name="ck_student_needs_maslow_level",
        ),
        CheckConstraint(
            "severity IN ('must_have','strong_preference','nice_to_have')",
            name="ck_student_needs_severity",
        ),
        CheckConstraint(
            "source IN ('discovery','manual','inferred')",
            name="ck_student_needs_source",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_student_needs_confidence",
        ),
        CheckConstraint(
            "(source = 'discovery' AND source_session_id IS NOT NULL)"
            " OR (source = 'manual' AND source_session_id IS NULL)"
            " OR (source = 'inferred')",
            name="ck_student_needs_source_provenance",
        ),
        Index("ix_student_needs_student_maslow", "student_id", "maslow_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    maslow_level: Mapped[str] = mapped_column(String(30), nullable=False)
    need_type: Mapped[str] = mapped_column(String(120), nullable=False)
    signal: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    source_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
    )
    source_quote: Mapped[str | None] = mapped_column(Text)
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
