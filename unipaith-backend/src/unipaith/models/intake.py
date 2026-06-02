"""Spec 44 — Adaptive Intake Engine storage (the §2 four-layer model).

The engine turns every student input channel (discovery chat, profile forms,
document uploads, external links, institution requirements, system-derived
flags) into normalized Prompt-Library signals carrying provenance, confidence,
and version history — without a 200-field form.

Four layers (§2), bottom-up:

    raw_inputs          immutable original answers/files/links + timestamps
    student_signals     normalized canonical layer (the value consumers read)
    signal_change_events append-only audit ledger (§9.6, separate from ai ledger)
    signal_clarifications low-confidence (<60) confirm/correct queue (§6)

The normalized layer reuses the Spec 42 ``SignalRecordMixin`` provenance
envelope (``models/base.py``) so every signal answers "where did this come
from, how sure are we, which write produced it, what's the audit chain".
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import (
    SIGNAL_SOURCE_CHECK_SQL,
    SIGNAL_SOURCES,
    Base,
    SignalRecordMixin,
)

# Intake channels (§5). One row per ingestion call carries its channel so the
# audit ledger and analytics can attribute a signal back to how it arrived.
INTAKE_CHANNELS = (
    "discovery_chat",  # §5.1
    "form",  # §5.2
    "document",  # §5.3
    "external_link",  # §5.4
    "institution",  # §5.5
    "system",  # §5.6
)
_CHANNEL_CHECK_SQL = "channel IN (" + ",".join(f"'{c}'" for c in INTAKE_CHANNELS) + ")"

# Lifecycle markers written to signal_change_events.event (§9.6).
CHANGE_EVENTS = (
    "created",
    "updated",
    "reconciled_kept",  # incoming lost the §7 source-priority duel; existing kept
    "confirmed",  # clarification confirmed → confidence bumped
    "corrected",  # clarification corrected → new value
)

CLARIFICATION_STATUSES = ("open", "confirmed", "corrected")


class RawInput(Base):
    """Immutable raw-inputs layer (§2 / §3.3).

    One row per ingested value, never updated. Lets the engine replay
    normalization if the extractor improves (§12) and is the anchor for every
    signal's ``raw_input_ref`` / provenance chain.
    """

    __tablename__ = "raw_inputs"
    __table_args__ = (
        CheckConstraint(_CHANNEL_CHECK_SQL, name="ck_raw_inputs_channel"),
        CheckConstraint(SIGNAL_SOURCE_CHECK_SQL, name="ck_raw_inputs_source"),
        Index("ix_raw_inputs_student_created", "student_id", "created_at"),
        Index("ix_raw_inputs_student_signal", "student_id", "signal_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    # Target signal when known (None for a raw chat turn that maps to many).
    signal_name: Mapped[str | None] = mapped_column(String(80))
    # The original value/payload exactly as received (text, parsed dict, url…).
    raw_value: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="student-typed")
    # Pointer to the external artifact (discovery_message id, S3 file ref, url).
    raw_input_ref: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StudentSignal(Base, SignalRecordMixin):
    """Normalized canonical layer (§2) — the single value consumers read (§9.1).

    Exactly one row per (student, signal_name). The domain value lives in
    ``value`` (JSONB so it fits any shape); the ``SignalRecordMixin`` columns
    carry the §5 provenance envelope. ``record_version`` is monotonic (§9.3).
    """

    __tablename__ = "student_signals"
    __table_args__ = (
        UniqueConstraint("student_id", "signal_name", name="uq_student_signals_student_signal"),
        CheckConstraint(SIGNAL_SOURCE_CHECK_SQL, name="ck_student_signals_source"),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 100", name="ck_student_signals_confidence_range"
        ),
        Index("ix_student_signals_student", "student_id"),
        Index("ix_student_signals_student_category", "student_id", "category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    signal_name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="other")
    # Current canonical value. JSONB-wrapped: scalars stored as {"v": ...}.
    value: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SignalChangeEvent(Base):
    """Append-only audit ledger (§9.6) — one row per signal write.

    Separate from the ``ai_audit_ledger`` so a compliance audit can trace every
    normalized-signal change independent of LLM activity.
    """

    __tablename__ = "signal_change_events"
    __table_args__ = (
        CheckConstraint(_CHANNEL_CHECK_SQL, name="ck_signal_change_events_channel"),
        Index("ix_signal_change_events_student_created", "student_id", "created_at"),
        Index("ix_signal_change_events_student_signal", "student_id", "signal_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    signal_name: Mapped[str] = mapped_column(String(80), nullable=False)
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    event: Mapped[str] = mapped_column(String(20), nullable=False, default="updated")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SignalClarification(Base):
    """Low-confidence confirm/correct queue (§6).

    When a normalized signal lands with confidence < 60 the engine opens a
    clarification so Discover can ask "Just to confirm — did you mean X?". The
    partial-unique index keeps at most one *open* clarification per signal.
    """

    __tablename__ = "signal_clarifications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','confirmed','corrected')",
            name="ck_signal_clarifications_status",
        ),
        Index(
            "uq_signal_clarifications_one_open",
            "student_id",
            "signal_name",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
        Index("ix_signal_clarifications_student_status", "student_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    signal_name: Mapped[str] = mapped_column(String(80), nullable=False)
    raw_value: Mapped[dict | None] = mapped_column(JSONB)
    suggested_value: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="open")
    resolved_value: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


__all__ = [
    "INTAKE_CHANNELS",
    "CHANGE_EVENTS",
    "CLARIFICATION_STATUSES",
    "SIGNAL_SOURCES",
    "RawInput",
    "StudentSignal",
    "SignalChangeEvent",
    "SignalClarification",
]
