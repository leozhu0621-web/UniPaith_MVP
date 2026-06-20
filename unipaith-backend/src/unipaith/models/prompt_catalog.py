"""Prompt catalog — the data-driven Prompt Library (widget spec §6).

One row per prompt: the counselor-voiced question, its widget (``ask_kind``),
the value type that drives quantify/write-typing, the fixed options (for
choice/multi/keywords), tier/section, display logic, and the My Space field it
``saves_to``. This table replaces the hard-coded ``enrichment_planner.CATALOG``
as the source of truth; ``CatalogService`` loads it in the shape the pure
planner consumes, and a later Airtable sync upserts into it. The in-code
``CATALOG`` constant remains the idempotent seed (insert-if-absent), so Airtable
edits are never clobbered by re-seeding.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
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

from unipaith.models.base import Base


class PromptCatalog(Base):
    __tablename__ = "prompt_catalog"
    __table_args__ = (
        UniqueConstraint("key", name="uq_prompt_catalog_key"),
        Index("ix_prompt_catalog_active_sort", "active", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(60), nullable=False)
    section: Mapped[str] = mapped_column(String(40), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    ask_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    display_logic: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False
    )
    saves_to: Mapped[str] = mapped_column(String(60), nullable=False)
    reference_source: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    airtable_record_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
