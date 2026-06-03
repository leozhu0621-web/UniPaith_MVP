"""
Phase 3 workflow models.
Only tables that don't already exist in Phase 1.
Notification, NotificationPreference, Touchpoint.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base


class Notification(Base):
    """In-app + email notification records."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
        Index("ix_notifications_created", "created_at"),
        # Spec 57 §3 — idempotency: a given source event writes at most one row,
        # even if its hook fires twice. Partial so legacy rows (NULL event_id)
        # don't collide.
        Index(
            "uq_notifications_event_id",
            "event_id",
            unique=True,
            postgresql_where=text("event_id IS NOT NULL"),
        ),
        # Spec 57 §6 — the digest job scans pending digest-class rows by urgency.
        Index("ix_notifications_user_urgency_emailed", "user_id", "urgency", "is_emailed"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(500))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_emailed: Mapped[bool] = mapped_column(Boolean, default=False)
    # Spec 57 §3 — stable idempotency key for the source event (e.g.
    # "decision_made:<application_id>"); NULL for ad-hoc notifications.
    event_id: Mapped[str | None] = mapped_column(String(200))
    # Spec 57 §6 — urgent (immediate) | digest (batched). Defaults urgent so any
    # legacy/unclassified notification keeps firing right away.
    urgency: Mapped[str] = mapped_column(
        String(20), default="urgent", server_default="urgent", nullable=False
    )
    # Spec 57 §4 — per-channel delivery outcomes ({channel: sent|failed|skipped}),
    # written by the delivery wrapper for observability + the DLQ.
    delivery_status: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User", backref="notifications")  # type: ignore[name-defined]  # noqa: F821


class NotificationPreference(Base):
    """Per-user notification preferences."""

    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Per-channel × per-type matrix (Spec 21 §2.4): {type: {email,sms,in_app,push}}.
    # Legacy rows hold a flat {type: bool} map — normalised on read by the service.
    preferences: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # all | weekly | important | none  (Spec 21 §2.4 / 42 §3.1)
    email_frequency: Mapped[str] = mapped_column(
        String(20), default="all", server_default="all", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", backref="notification_preferences")  # type: ignore[name-defined]  # noqa: F821


class Touchpoint(Base):
    """
    Automatic CRM record of every meaningful interaction.
    Logged by event hooks — never manually by the user.
    """

    __tablename__ = "touchpoints"
    __table_args__ = (
        Index("ix_touchpoints_student", "student_id"),
        Index("ix_touchpoints_institution", "institution_id"),
        Index("ix_touchpoints_application", "application_id"),
        Index("ix_touchpoints_type", "touchpoint_type"),
        Index("ix_touchpoints_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="SET NULL")
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL")
    )
    touchpoint_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
