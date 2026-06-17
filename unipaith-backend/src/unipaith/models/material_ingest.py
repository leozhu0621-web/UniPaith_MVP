"""Material ingest — "upload any file, Uni reads it, turns it into My Space."

A `MaterialIngest` row records one uploaded document (resume / transcript / CV /
essay), the AI's structured reading of it (`proposed`), and what the student
confirmed into their profile (`applied_summary`). The raw file is parsed
in-memory and not retained here (durable file storage is the `documents`
feature); this table is the review-and-confirm ledger.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

MATERIAL_INGEST_STATUSES = ("parsed", "applied", "failed")


class MaterialIngest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "material_ingests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('parsed','applied','failed')",
            name="ck_material_ingests_status",
        ),
        Index("ix_material_ingests_student", "student_id"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str | None] = mapped_column(String(512))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="parsed")
    # The AI's structured reading: {profile, academic_records, test_scores,
    # activities, work_experiences, goals, needs, identity, summary}.
    proposed: Mapped[dict | None] = mapped_column(JSONB)
    # What was written to My Space on confirm: {counts:{...}, applied_at}.
    applied_summary: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
