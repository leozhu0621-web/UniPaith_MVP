"""Session templates — guided work-orders for the Uni advisor chat (spec §5/§6).

A template is an ordered list of steps, each either a ``prompt`` (a question
from the enrichment_planner CATALOG, by its key) or an ``action`` (a
code-backed capability). Templates end in an artifact and are driven by
TEMPLATE_LIBRARY seed data; Airtable can later upsert into both tables via
``airtable_record_id``.
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


class SessionTemplate(Base):
    __tablename__ = "session_templates"
    __table_args__ = (
        UniqueConstraint("key", name="uq_session_templates_key"),
        Index("ix_session_templates_active_sort", "active", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    topic: Mapped[str] = mapped_column(String(30), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome: Mapped[str] = mapped_column(String(160), nullable=False)
    icon: Mapped[str] = mapped_column(String(30), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    airtable_record_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    steps: Mapped[list[SessionTemplateStep]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="SessionTemplateStep.step_order",
    )


class SessionTemplateStep(Base):
    __tablename__ = "session_template_steps"
    __table_args__ = (
        CheckConstraint("step_type IN ('prompt','action')", name="ck_session_template_steps_type"),
        CheckConstraint(
            "(prompt_key IS NULL) <> (action_key IS NULL)",
            name="ck_session_template_steps_exactly_one_key",
        ),
        Index("ix_session_template_steps_template_order", "template_id", "step_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(10), nullable=False)
    prompt_key: Mapped[str | None] = mapped_column(String(60), nullable=True)
    action_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    airtable_record_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    template: Mapped[SessionTemplate] = relationship(back_populates="steps")
