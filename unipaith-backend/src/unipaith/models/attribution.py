from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base

# Spec 28 §2 — attribution taxonomy. Kept as plain strings (not DB enums) to
# match the codebase convention (no enum-type accumulation flake) and to let new
# source kinds / actions land without a migration.
SOURCE_KINDS = (
    "institution_page",
    "program_page",
    "post",
    "event",
    "campaign",
    "promotion",
)
ATTRIBUTION_ACTIONS = (
    "impression",
    "view",
    "click",
    "save",
    "unsave",
    "compare",
    "request_info",
    "rsvp",
    "attendance",
    "apply_started",
    "submitted",
    "decision_outcome",
)


class AttributionEvent(Base):
    """Spec 28 §8 — one row per student action that COULD carry a source.

    The canonical event-sourced store the analytics module reads aggregate from.
    Written best-effort by ``AttributionService.record`` (wired into the existing
    engagement / campaign / application action sites) and backfilled from the
    durable domain tables so the funnel is meaningful on day-one data.

    Filters (program / intake / segment / campaign / time) apply uniformly
    because every row carries ``program_id`` / ``campaign_id`` / ``occurred_at``
    (+ ``student_id`` for segment-membership resolution at read time).
    """

    __tablename__ = "attribution_events"
    __table_args__ = (
        Index("ix_attribution_inst_occurred", "institution_id", "occurred_at"),
        Index("ix_attribution_inst_action", "institution_id", "action"),
        Index("ix_attribution_inst_source", "institution_id", "source_kind", "source_id"),
        Index("ix_attribution_inst_campaign", "institution_id", "campaign_id"),
        Index("ix_attribution_inst_program", "institution_id", "program_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable: anonymous / not-yet-resolved actors (e.g. external-email clicks).
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="SET NULL"),
    )
    # institution_page | program_page | post | event | campaign | promotion
    source_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    # The concrete source object id (post/event/promotion/campaign/program/
    # institution). Not a FK — polymorphic by ``source_kind``.
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(30), nullable=False)

    # Dimensions for breakdown (Spec 28 §5). All nullable — populated when known
    # at write time, otherwise resolved at read time (segment via membership,
    # intake via date window).
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    intake_round_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intake_rounds.id", ondelete="SET NULL")
    )
    segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_segments.id", ondelete="SET NULL")
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    meta: Mapped[dict | None] = mapped_column(JSONB)
    # Stable idempotency key so the domain backfill never double-inserts a row
    # (e.g. ``app_submitted:<application_id>``). NULL for live-tracked events.
    dedupe_key: Mapped[str | None] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
