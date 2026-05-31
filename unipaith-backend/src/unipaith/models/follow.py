from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class InstitutionFollow(Base):
    """A student explicitly following an institution (Spec 12 §10 / Spec 20).

    Distinct from saving a *program*: a follow is institution-level intent that
    drives the Connect feed independent of saves. The Connect feed unions these
    explicit follows with the institutions of saved programs (back-compat).
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
