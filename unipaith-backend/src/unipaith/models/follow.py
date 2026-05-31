from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base

# Spec 20 §2 — how a follow came to exist. Drives the unfollow-block rule:
# an ``application`` follow cannot be removed while the application is active.
FOLLOW_SOURCES = ("saved", "application", "explicit")


class InstitutionFollow(Base):
    """A student following an institution (Spec 12 §10 / Spec 20 §2).

    This is the ``Follow`` of Spec 20 §7 (the doc names a ``student_follows``
    table; we extend the existing ``institution_follows`` rather than fork a
    parallel one). A follow is institution-level intent that drives the Connect
    feed. ``program_id`` records which program triggered an auto-follow (null
    for an institution-level explicit follow). ``muted`` keeps the follow row
    (so application context survives) while suppressing its feed items.
    """

    __tablename__ = "institution_follows"
    __table_args__ = (
        UniqueConstraint("student_id", "institution_id", name="uq_institution_follow"),
        Index("ix_institution_follows_student", "student_id"),
        Index("ix_institution_follows_institution", "institution_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The program whose save/apply triggered this follow (Spec 20 §2). Null for
    # an institution-level explicit follow from a school page.
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    # 'saved' | 'application' | 'explicit' (Spec 20 §2 / §7).
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="explicit", server_default=text("'explicit'")
    )
    # Muting suppresses feed items but keeps the follow (Spec 20 §2). Note: a
    # ``program_change`` item is never suppressed by mute (Spec 20 §4.3).
    muted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
