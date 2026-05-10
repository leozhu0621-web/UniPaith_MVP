"""Phase D1 — AI turn feedback ledger.

Captures explicit user signal on every AI surface (orchestrator turns,
extractor outputs students see, rationale text, workshop coach output).
Used by:
  - The weekly review pipeline — low-vote turns become candidates for
    extractor-fixture expansion or prompt iteration.
  - Per-student safety profile — repeated thumbs-down patterns flag the
    student for human review.
  - Cost-of-quality dashboards — what does the user actually find
    useful vs. tolerate?

Design choices
--------------
- One row per (student, surface, target_id, vote) — students can change
  their vote (latest wins) but we keep history. The unique constraint
  is on (student_id, target_id, surface) so updates upsert.
- `target_id` is loosely typed — references can point at AiTurn,
  DiscoveryMessage, MatchResult, or StudentEssay rows depending on
  surface. We keep it as UUID without a hard FK because the targets
  span tables.
- Free-text is capped at 1k chars; longer reasons go in
  `ai_safety_incidents` with admin attention.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class AiTurnFeedback(Base):
    """Per-turn thumbs / regenerate / 'not right' feedback from students."""

    __tablename__ = "ai_turn_feedback"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "target_id",
            "surface",
            name="uq_ai_feedback_student_target_surface",
        ),
        CheckConstraint(
            "vote IN ('up','down','regenerate','not_right')",
            name="ck_ai_feedback_vote",
        ),
        CheckConstraint(
            "surface IN ('orchestrator_turn','extractor_signal',"
            "'rationale','workshop_essay','workshop_interview',"
            "'workshop_test_prep','match_card','other')",
            name="ck_ai_feedback_surface",
        ),
        Index("ix_ai_feedback_surface_created", "surface", "created_at"),
        Index("ix_ai_feedback_student_created", "student_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Loose reference — `target_id` may point at AiTurn, DiscoveryMessage,
    # MatchResult, or StudentEssay depending on `surface`. No FK so we
    # don't have to maintain N FKs and can add new surfaces freely.
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    surface: Mapped[str] = mapped_column(String(40), nullable=False)
    vote: Mapped[str] = mapped_column(String(20), nullable=False)
    # 'too_generic', 'not_specific', 'wrong_facts', 'tone',
    # 'asked_for_rewrite', 'helpful', etc. — controlled vocabulary
    # documented in the API schema. Free-form for forward compatibility.
    reason_category: Mapped[str | None] = mapped_column(String(40))
    free_text: Mapped[str | None] = mapped_column(Text)
    # Free-form context dict — e.g. for orchestrator_turn, the layer
    # the student was on. Used by the weekly review for slicing.
    context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
