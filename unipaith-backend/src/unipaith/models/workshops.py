"""Phase A — Workshop feedback model.

Replaces the generation-style essay/resume workshops. The output schema has
NO field that could carry prose generation back to the student — see
WorkshopFeedbackResponse and test_workshop_no_generation_contract.py for the
mechanical guarantee.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class WorkshopFeedbackRun(Base):
    __tablename__ = "workshop_feedback_runs"
    __table_args__ = (
        CheckConstraint(
            "domain IN ('essay','interview','test')",
            name="ck_workshop_feedback_runs_domain",
        ),
        Index(
            "ix_workshop_feedback_runs_student_domain",
            "student_id",
            "domain",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    input_artifact_id: Mapped[str | None] = mapped_column(String(120))
    prompt_text: Mapped[str | None] = mapped_column(Text)
    rubric_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    structural_issues: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    missing_elements: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    suggested_questions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
