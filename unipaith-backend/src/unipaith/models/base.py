import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# Spec 42 §5 — the universal record metadata every signal carries. The domain
# value(s) live on the owning table's own columns; this mixin adds the
# provenance envelope so any signal can answer "where did this come from, how
# sure are we, which write produced it, and what's the audit chain".
#
# `record_version` is deliberately distinct from any domain-level "version" the
# row may also track (e.g. a draft's `version_count`): this counts writes to the
# record, theirs counts user-facing revisions.
#
# Allowed `source` values (Spec 42 §2 / §5). Reused as the CHECK body by each
# table that mixes this in (constraint names must be table-unique, so the
# constraint itself is declared per-table, not here).
SIGNAL_SOURCES = (
    "student-typed",
    "student-uploaded",
    "student-link",
    "student-derived",
    "institution-supplied",
    "system-derived",
    "system-extracted",
    "third-party-verified",
)
SIGNAL_SOURCE_CHECK_SQL = "source IN (" + ",".join(f"'{s}'" for s in SIGNAL_SOURCES) + ")"


class SignalRecordMixin:
    """Spec 42 §5 — provenance / confidence / version envelope for a signal."""

    source: Mapped[str] = mapped_column(String(32), nullable=False, default="student-typed")
    # 0–100. Defaults follow §5's confidence rules (set explicitly by services).
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    # Normalized-for-matching form of the value(s), when normalization applies
    # (e.g. STAR booleans rolled up, free-text → tags). JSON so it fits any shape.
    value_normalized: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Pointer to the raw input that produced the value (file ref, message id…).
    raw_input_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Append-only [{event, timestamp, actor}] audit chain (§5 / §7).
    provenance_chain: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
