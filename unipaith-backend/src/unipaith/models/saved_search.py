"""SavedSearch model (Spec 56 §6 — Saved searches + alerts).

The one net-new persistence Spec 56 calls for. A student names a search/filter
set; if ``alert_enabled`` the scheduled alert loop re-runs it against the
(crawler-freshened) index and notifies on new matches — the proactive payoff
that pairs with the Connect feed (Spec 56 §6, Spec 60 §3B).

``query`` is the serialized ``SearchRequest`` shape (``q`` + ``chips`` +
``filters`` + ``sort``) so a saved search restores the exact Explore state and
the alert loop can replay it deterministically. ``entity_type`` scopes what the
search targets; ``program`` is wired today, ``scholarship`` / ``school`` are
accepted now so the schema doesn't churn when their indexes land.
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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# What a saved search targets. Only ``program`` is index-backed today; the
# others are accepted so adding their search later needs no migration.
SAVED_SEARCH_ENTITY_TYPES = ("program", "scholarship", "school")


class SavedSearch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "saved_searches"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('program', 'scholarship', 'school')",
            name="ck_saved_searches_entity_type",
        ),
        # The alert loop scans alert_enabled rows; the partial index keeps that
        # scan cheap as the table grows.
        Index(
            "ix_saved_searches_alert_enabled",
            "alert_enabled",
            postgresql_where="alert_enabled",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, default="program")
    # Serialized SearchRequest: {query, chips, filters, sort}.
    query: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    alert_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Alert-loop bookkeeping. last_match_count is the baseline the next run
    # diffs against to decide "new matches"; last_alerted_at + the daily count
    # of saved_search_alert notifications enforce the per-user cap (§6).
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_match_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
