"""Phase A — Student identity model (deepest profile layer).

Single row per student (PK = student_id). The three JSONB columns hold lists
of provenance-tagged dicts:

  core_values:    [{value, evidence, confidence, source_quote}]
  worldview:      [{belief, context, confidence, source_quote}]
  self_awareness: [{insight, trigger_event, confidence, source_quote}]

`identity_summary` is LLM-written prose that's regenerated when the structured
fields change. Plan 2 owns regeneration; Phase A's stub just marks it.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class StudentIdentity(Base):
    __tablename__ = "student_identity"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    core_values: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    worldview: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    self_awareness: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    identity_summary: Mapped[str | None] = mapped_column(Text)
    last_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
