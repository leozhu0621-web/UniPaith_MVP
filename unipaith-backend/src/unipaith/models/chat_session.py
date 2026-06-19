"""Uni chat-tab sessions + folders (2026-06-19 chat-tab redesign, spec §3).

The organization layer for the Advisor chat: named sessions filed into preset
(white-paper-topic) or custom folders. The conversation transcript itself lives
in the managed-agent / discovery layer (linked via ``agent_session_id``); this
model owns titling, foldering, pin/order, and context-spawn provenance.
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
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base

# White-paper topic keys (the preset folders) and the stage each sits under.
TOPIC_STAGE: dict[str, str] = {
    "profile": "discovery",
    "goals": "discovery",
    "needs": "discovery",
    "strategy": "recommendation",
    "schools": "recommendation",
    "connect": "application",
    "prepare": "application",
    "manage": "application",
}


class ChatFolder(Base):
    __tablename__ = "chat_folders"
    __table_args__ = (
        CheckConstraint("kind IN ('preset','custom')", name="ck_chat_folders_kind"),
        CheckConstraint(
            "(kind = 'preset') = (topic_key IS NOT NULL)",
            name="ck_chat_folders_preset_has_topic",
        ),
        UniqueConstraint("student_id", "topic_key", name="uq_chat_folders_student_topic"),
        Index("ix_chat_folders_student_sort", "student_id", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="custom")
    topic_key: Mapped[str | None] = mapped_column(String(30))  # preset only
    stage: Mapped[str | None] = mapped_column(String(20))  # preset only
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    sessions: Mapped[list[ChatSession]] = relationship(
        back_populates="folder", cascade="all, delete-orphan"
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('active','archived')", name="ck_chat_sessions_status"),
        Index("ix_chat_sessions_folder_sort", "folder_id", "sort_order"),
        Index("ix_chat_sessions_student_pinned", "student_id", "pinned"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    folder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_folders.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # context-spawn provenance: kind in {manual, discover_program, discover_school,
    # scholarship, event, peer, upload, ...}; ref = the source object id/slug.
    origin_kind: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    origin_ref: Mapped[str | None] = mapped_column(String(255))
    agent_session_id: Mapped[str | None] = mapped_column(String(64))  # managed-agent link
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    folder: Mapped[ChatFolder] = relationship(back_populates="sessions")
