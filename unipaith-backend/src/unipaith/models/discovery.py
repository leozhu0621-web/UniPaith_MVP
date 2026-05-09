"""Phase A — Discovery models.

Storage backbone for the Stage 1 (Discovery) journey. The Discovery LLM
(Plan 2) is the producer of `assistant`-role messages and `extracted_signals`;
Phase A only defines the storage and contract.

Tracks: 'profile' | 'goals' | 'needs'.
Layers (only for track='profile'): 'basic' | 'personality' | 'identity'.
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base


class DiscoverySession(Base):
    __tablename__ = "discovery_sessions"
    __table_args__ = (
        CheckConstraint(
            "track IN ('profile','goals','needs')",
            name="ck_discovery_sessions_track",
        ),
        CheckConstraint(
            "layer IS NULL OR layer IN ('basic','personality','identity')",
            name="ck_discovery_sessions_layer",
        ),
        CheckConstraint(
            "status IN ('active','completed','abandoned')",
            name="ck_discovery_sessions_status",
        ),
        CheckConstraint(
            "completion_pct >= 0 AND completion_pct <= 1",
            name="ck_discovery_sessions_completion_pct",
        ),
        CheckConstraint(
            "(track = 'profile') OR (layer IS NULL)",
            name="ck_discovery_sessions_layer_only_for_profile",
        ),
        Index(
            "ix_discovery_sessions_student_track_status",
            "student_id",
            "track",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    track: Mapped[str] = mapped_column(String(20), nullable=False)
    layer: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    completion_pct: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, default=Decimal("0")
    )
    exit_signal: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    messages: Mapped[list[DiscoveryMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DiscoveryMessage.created_at",
    )


class DiscoveryMessage(Base):
    __tablename__ = "discovery_messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('student','assistant','system')",
            name="ck_discovery_messages_role",
        ),
        Index(
            "ix_discovery_messages_session_created",
            "session_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_signals: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[DiscoverySession] = relationship(back_populates="messages")
