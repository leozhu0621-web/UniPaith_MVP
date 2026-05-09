"""Phase A — Student strategy model.

Versioned per student. Partial unique index `uq_student_strategies_one_active`
(defined in the migration) enforces "at most one active row per student" —
SQLAlchemy doesn't model partial indexes in __table_args__ cleanly, but the
constraint exists at the DB level.
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
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class StudentStrategy(Base):
    __tablename__ = "student_strategies"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','active','archived')",
            name="ck_student_strategies_status",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_student_strategies_version_positive",
        ),
        UniqueConstraint("student_id", "version", name="uq_student_strategies_student_version"),
        Index(
            "ix_student_strategies_student_status",
            "student_id",
            "status",
        ),
        # Partial unique index: at most one active strategy per student.
        # Mirrored in the alembic migration so prod DBs and test DBs (which
        # use Base.metadata.create_all) both get the constraint. The service
        # layer also archives the previous active row before activating a new
        # one to avoid IntegrityError on the happy path.
        Index(
            "uq_student_strategies_one_active",
            "student_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    career_target: Mapped[str | None] = mapped_column(Text)
    target_degree: Mapped[str | None] = mapped_column(String(120))
    academic_path: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    financial_path: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    geographic_path: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    narrative: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    generated_from_session_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    is_stub: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
