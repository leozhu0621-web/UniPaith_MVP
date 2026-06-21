from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class MySpaceTaskState(Base):
    """Student-owned presentation state for My Space tasks.

    Completion stays with the owning domain endpoint. This table only stores
    dismiss/snooze preferences for computed tasks.
    """

    __tablename__ = "my_space_task_states"
    __table_args__ = (
        UniqueConstraint("student_id", "task_key", name="uq_my_space_task_states_student_task"),
        Index("ix_my_space_task_states_student_task", "student_id", "task_key"),
        Index(
            "ix_my_space_task_states_student_visibility",
            "student_id",
            "dismissed",
            "snoozed_until",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_key: Mapped[str] = mapped_column(String(180), nullable=False)
    dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
