"""Spec 42 §3.19–§3.20 / §8 — Prompt Library + Story Bank.

The behavioral-prompt layer is distinct from Workshops (`14`): Workshops give
feedback on a draft; this is the *catalog* of canonical behavioral prompts plus
the student's *responses* and a reusable *story bank*, all stored as durable
profile signals carrying the universal record metadata (Spec 42 §5,
``SignalRecordMixin``).

Three tables (§8):
- ``behavioral_prompts``           — platform-defined prompt catalog (seeded).
- ``student_behavioral_responses`` — per-(student, prompt) response + STAR flags.
- ``student_stories``              — reusable narrative units mapped to prompts.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import (
    SIGNAL_SOURCE_CHECK_SQL,
    Base,
    SignalRecordMixin,
)

# ── Controlled vocabularies (Spec 42 §3.19 / §3.20) ──────────────────────────
# §3.19's base intent set, extended to cover the full ~70-prompt catalog from
# `Misc./Prompt Library.docx` (curiosity / resilience / service / teamwork /
# communication / identity round out the base nine).
INTENT_TAGS = (
    "leadership",
    "conflict",
    "failure",
    "impact",
    "ethics",
    "learning",
    "motivation",
    "fit",
    "vision",
    "curiosity",
    "resilience",
    "service",
    "teamwork",
    "communication",
    "identity",
)
TARGET_CHANNELS = ("interview", "essay", "short_answer", "video")
FORMATS = ("STAR", "CAR", "freeform")
CONFIDENTIALITY_SCOPES = ("private", "shareable", "recommender_facing")
REUSE_SCOPES = ("core", "school_specific")
DRAFT_STATUSES = ("none", "draft", "revised", "final")
IMPACT_METRIC_TYPES = ("count", "percent", "dollar", "time", "scale")
COMPETENCIES = (
    "leadership",
    "teamwork",
    "impact",
    "resilience",
    "creativity",
    "analytical",
    "communication",
    "initiative",
)
ROLE_TYPES = ("leader", "contributor", "founder", "observer")
STAKEHOLDER_TYPES = ("peers", "authority", "clients", "public", "self")
CONFLICT_TYPES = ("interpersonal", "resource", "ethical", "technical", "time", "none")


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN (" + ",".join(f"'{v}'" for v in values) + ")"


class BehavioralPrompt(Base):
    """Platform-defined prompt catalog (Spec 42 §3.19 per-prompt metadata)."""

    __tablename__ = "behavioral_prompts"
    __table_args__ = (
        CheckConstraint(_in("intent_tag", INTENT_TAGS), name="ck_behavioral_prompts_intent"),
        CheckConstraint(
            _in("target_channel", TARGET_CHANNELS), name="ck_behavioral_prompts_channel"
        ),
        CheckConstraint(_in("format_required", FORMATS), name="ck_behavioral_prompts_format"),
        CheckConstraint(
            _in("confidentiality_scope", CONFIDENTIALITY_SCOPES),
            name="ck_behavioral_prompts_confidentiality",
        ),
        CheckConstraint(
            _in("reuse_allowed_flag", REUSE_SCOPES), name="ck_behavioral_prompts_reuse"
        ),
        Index("ix_behavioral_prompts_active_sort", "is_active", "sort_order"),
        Index("ix_behavioral_prompts_intent", "intent_tag"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Stable slug — the natural key responses reference. Unique catalog id.
    prompt_key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    intent_tag: Mapped[str] = mapped_column(String(20), nullable=False)
    target_channel: Mapped[str] = mapped_column(String(16), nullable=False, default="interview")
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer)
    word_limit: Mapped[int | None] = mapped_column(Integer)
    format_required: Mapped[str] = mapped_column(String(10), nullable=False, default="STAR")
    evidence_required_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_attachments_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    language_option: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    confidentiality_scope: Mapped[str] = mapped_column(
        String(20), nullable=False, default="private"
    )
    reuse_allowed_flag: Mapped[str] = mapped_column(String(16), nullable=False, default="core")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class StudentStory(Base, SignalRecordMixin):
    """Reusable narrative unit the student maps to prompts/essays (Spec 42 §3.20)."""

    __tablename__ = "student_stories"
    __table_args__ = (
        CheckConstraint(
            "primary_competency IS NULL OR " + _in("primary_competency", COMPETENCIES),
            name="ck_student_stories_primary_competency",
        ),
        CheckConstraint(
            "secondary_competency IS NULL OR " + _in("secondary_competency", COMPETENCIES),
            name="ck_student_stories_secondary_competency",
        ),
        CheckConstraint(
            "role_type IS NULL OR " + _in("role_type", ROLE_TYPES),
            name="ck_student_stories_role_type",
        ),
        CheckConstraint(
            "stakeholder_type IS NULL OR " + _in("stakeholder_type", STAKEHOLDER_TYPES),
            name="ck_student_stories_stakeholder_type",
        ),
        CheckConstraint(
            "conflict_type IS NULL OR " + _in("conflict_type", CONFLICT_TYPES),
            name="ck_student_stories_conflict_type",
        ),
        CheckConstraint(
            "difficulty_tier IS NULL OR (difficulty_tier BETWEEN 1 AND 5)",
            name="ck_student_stories_difficulty_tier",
        ),
        CheckConstraint(
            "scale_tier IS NULL OR (scale_tier BETWEEN 1 AND 5)",
            name="ck_student_stories_scale_tier",
        ),
        CheckConstraint(SIGNAL_SOURCE_CHECK_SQL, name="ck_student_stories_source"),
        Index("ix_student_stories_student", "student_id"),
        Index("ix_student_stories_student_competency", "student_id", "primary_competency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    primary_competency: Mapped[str | None] = mapped_column(String(20))
    secondary_competency: Mapped[str | None] = mapped_column(String(20))
    competency_tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    context_tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    role_type: Mapped[str | None] = mapped_column(String(16))
    stakeholder_type: Mapped[str | None] = mapped_column(String(16))
    conflict_type: Mapped[str | None] = mapped_column(String(16))
    difficulty_tier: Mapped[int | None] = mapped_column(Integer)
    recency: Mapped[date | None] = mapped_column(Date)
    duration: Mapped[str | None] = mapped_column(String(80))
    scale_tier: Mapped[int | None] = mapped_column(Integer)
    evidence_link: Mapped[str | None] = mapped_column(String(500))
    referenceable_contact_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class StudentBehavioralResponse(Base, SignalRecordMixin):
    """A student's response to a behavioral prompt (Spec 42 §3.19 per-response).

    ``prompt_key`` is a soft reference to the platform-managed catalog (the
    catalog is seeded/owned by the platform, never user-deleted), kept indexed
    for join-free lookups. STAR + impact flags are system-derived on save.
    """

    __tablename__ = "student_behavioral_responses"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "prompt_key", name="uq_student_behavioral_responses_student_prompt"
        ),
        CheckConstraint(
            _in("draft_status", DRAFT_STATUSES), name="ck_student_behavioral_responses_draft"
        ),
        CheckConstraint(
            "confidence_self_rating IS NULL OR (confidence_self_rating BETWEEN 1 AND 5)",
            name="ck_student_behavioral_responses_self_rating",
        ),
        CheckConstraint(
            "impact_metric_type IS NULL OR " + _in("impact_metric_type", IMPACT_METRIC_TYPES),
            name="ck_student_behavioral_responses_impact_type",
        ),
        CheckConstraint(SIGNAL_SOURCE_CHECK_SQL, name="ck_student_behavioral_responses_source"),
        Index("ix_student_behavioral_responses_student", "student_id"),
        Index(
            "ix_student_behavioral_responses_student_status",
            "student_id",
            "draft_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt_key: Mapped[str] = mapped_column(String(80), nullable=False)
    response_text: Mapped[str | None] = mapped_column(Text)
    draft_status: Mapped[str] = mapped_column(String(12), nullable=False, default="none")
    last_edited: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_self_rating: Mapped[int | None] = mapped_column(Integer)
    authenticity_confidence_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    needs_feedback_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewer_feedback_received_flag: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # STAR completeness (system-derived on save).
    star_situation_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    star_task_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    star_action_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    star_result_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    star_reflection_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    impact_metric_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    impact_metric_type: Mapped[str | None] = mapped_column(String(10))
    impact_metric_value_band: Mapped[str | None] = mapped_column(String(40))
    linked_story_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_stories.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
