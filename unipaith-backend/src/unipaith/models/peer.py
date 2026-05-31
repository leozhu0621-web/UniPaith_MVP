"""Peer connection models — Spec 20 §6 (opt-in, privacy-gated Peers tab).

Privacy invariant (Spec 20 §6.2): the peer-visibility sub-profile is SEPARATE
from the application profile and **structurally excludes** any field that could
leak scores, GPA, documents, decisions, or financials. The contract test
``tests/test_connect_peers.py`` asserts no such column ever exists here — the
same mechanical guarantee the Workshops module uses for the no-generation rule.

A peer is referenced externally by an opaque ``PeerProfile.id`` (Spec 20 §7
"peer_id; not the student_id").
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
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class PeerProfile(Base):
    """A student's opt-in, self-curated peer-visibility sub-profile (§6.2).

    Only the fields the student chooses to expose. NEVER scores / GPA /
    documents / decisions / financials.
    """

    __tablename__ = "peer_profiles"
    __table_args__ = (UniqueConstraint("student_id", name="uq_peer_profile_student"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    use_alias: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    intended_major: Mapped[str | None] = mapped_column(String(150))
    # General location only — country / region, NEVER an address (§6.2).
    region: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    # Whether to expose target programs (from saved/applied) on the peer card.
    share_targets: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    # Discoverable by other peers.
    visible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PeerConnection(Base):
    """A directed peer relationship (§6.3): connect request, accepted
    connection, or block. On accept a ``peer`` Inbox thread opens."""

    __tablename__ = "peer_connections"
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_peer_connection_pair"),
        Index("ix_peer_connections_addressee", "addressee_id"),
        Index("ix_peer_connections_requester", "requester_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    addressee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    # 'requested' | 'connected' | 'declined' | 'blocked'
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="requested", server_default=text("'requested'")
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PeerReport(Base):
    """A report on a peer (§6.3) — routes to a moderation queue (status='open')."""

    __tablename__ = "peer_reports"
    __table_args__ = (Index("ix_peer_reports_status", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    reported_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(50))
    detail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open", server_default=text("'open'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
