from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    ranking_data: Mapped[dict | None] = mapped_column(JSONB)
    description_text: Mapped[str | None] = mapped_column(Text)
    campus_description: Mapped[str | None] = mapped_column(Text)
    campus_setting: Mapped[str | None] = mapped_column(String(30))
    student_body_size: Mapped[int | None] = mapped_column(Integer)
    founded_year: Mapped[int | None] = mapped_column(Integer)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(String(2000))
    website_url: Mapped[str | None] = mapped_column(String(1000))
    media_gallery: Mapped[dict | None] = mapped_column(JSONB)
    social_links: Mapped[dict | None] = mapped_column(JSONB)
    inquiry_routing: Mapped[dict | None] = mapped_column(JSONB)
    support_services: Mapped[dict | None] = mapped_column(JSONB)
    policies: Mapped[dict | None] = mapped_column(JSONB)
    international_info: Mapped[dict | None] = mapped_column(JSONB)
    school_outcomes: Mapped[dict | None] = mapped_column(JSONB)
    claimed_from_source: Mapped[str | None] = mapped_column(String(50))
    claimed_extracted_ids: Mapped[dict | None] = mapped_column(JSONB)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # Spec 25 §7 — optional campaign approval step. When True, campaigns must
    # pass through `pending_approval` before they can be scheduled/sent.
    require_campaign_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    # Spec 30 — First-run setup wizard (/i/setup).
    # `setup_complete` gates the forced-onboarding redirect + dimmed nav.
    # `setup_state` persists wizard progress so the flow is resumable:
    #   {"step": 1|2|3|4|"done",
    #    "steps_complete": {"profile": bool, "program": bool, "data": bool, "team": bool},
    #    "skipped": {"data": bool, "team": bool},
    #    "first_program_id": str | None}
    setup_complete: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    setup_state: Mapped[dict | None] = mapped_column(JSONB)
    review_config: Mapped[dict | None] = mapped_column(JSONB)
    # Spec 37 (AI Extensibility) §5 / 46 §9 — per-institution AI controls:
    # per-surface enable toggles, per-surface confidence thresholds, and the
    # no-training tier override. NULL = all defaults (see
    # services/ai_config_service.DEFAULT_AI_CONFIG).
    ai_config: Mapped[dict | None] = mapped_column(JSONB)
    # Spec 39 (Fees & Payments) §2.1 — applicant-facing fee/deposit collection
    # config, edited at /i/settings?tab=billing. NULL = no fee, no deposit.
    #   {"application_fee": {"enabled": bool, "amount_cents": int, "currency": "USD"},
    #    "waiver": {"policy": "allow_and_reconcile" | "block_until_approved",
    #               "auto_rules": ["fee_waiver_code", "first_gen", "income_band", "nacac_sram"]},
    #    "enrollment_deposit": {"enabled": bool, "amount_cents": int, "currency": "USD",
    #                           "deadline_days": int, "refundable": bool,
    #                           "non_refundable_cents": int},
    #    "stripe_connect_account_id": str | null}
    # Effective amounts: program override (cost_data) → this config → none.
    payment_config: Mapped[dict | None] = mapped_column(JSONB)
    # Spec 46 §9 — institution data-governance config, edited at
    # /i/settings?tab=data. NULL = platform defaults (see
    # services/data_governance.DEFAULT_DATA_GOVERNANCE):
    #   {"override_expiry_weeks_default": int (1–4),
    #    "protected_attributes_tracked": [str],   # subset of the §6.1 set
    #    "no_training_tier": bool,                # force consent.training=false
    #    "data_residency": "us" | "canada" | "eu"}  # Phase 14 deferred, US only
    data_governance: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    admin_user: Mapped[User] = relationship("User", back_populates="institution")  # type: ignore[name-defined]  # noqa: F821
    programs: Mapped[list[Program]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    segments: Mapped[list[TargetSegment]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    campaigns: Mapped[list[Campaign]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    events: Mapped[list[Event]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    reviewers: Mapped[list[Reviewer]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    datasets: Mapped[list[InstitutionDataset]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    posts: Mapped[list[InstitutionPost]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    schools: Mapped[list[School]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    uploaded_lists: Mapped[list[UploadedList]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )
    campaign_suppressions: Mapped[list[CampaignSuppression]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )


class School(Base):
    """A school/college within a university (e.g. Stern School of Business within NYU)."""

    __tablename__ = "schools"
    __table_args__ = (
        Index("ix_schools_institution", "institution_id"),
        UniqueConstraint("institution_id", "name", name="uq_schools_institution_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description_text: Mapped[str | None] = mapped_column(Text)
    media_urls: Mapped[dict | None] = mapped_column(JSONB)
    logo_url: Mapped[str | None] = mapped_column(String(1000))
    sort_order: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="schools")
    programs: Mapped[list[Program]] = relationship(back_populates="school")


class Program(Base):
    __tablename__ = "programs"
    __table_args__ = (Index("ix_programs_institution_published", "institution_id", "is_published"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # Free-text department label (legacy, kept for back-compat).
    department: Mapped[str | None] = mapped_column(String(255))
    # Spec 41 §2.4 — link to the reviewing Department (graduate review portal +
    # funding pools). Nullable: undergrad programs and unmapped programs leave it
    # null. SET NULL so deleting a department doesn't cascade to programs.
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    duration_months: Mapped[int | None] = mapped_column(Integer)
    tuition: Mapped[int | None] = mapped_column(Integer)
    acceptance_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    delivery_format: Mapped[str | None] = mapped_column(String(30))
    campus_setting: Mapped[str | None] = mapped_column(String(30))
    requirements: Mapped[dict | None] = mapped_column(JSONB)
    application_requirements: Mapped[dict | None] = mapped_column(JSONB)
    description_text: Mapped[str | None] = mapped_column(Text)
    who_its_for: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    application_deadline: Mapped[date | None] = mapped_column(Date)
    program_start_date: Mapped[date | None] = mapped_column(Date)
    tracks: Mapped[dict | None] = mapped_column(JSONB)
    outcomes_data: Mapped[dict | None] = mapped_column(JSONB)
    intake_rounds: Mapped[dict | None] = mapped_column(JSONB)
    media_urls: Mapped[dict | None] = mapped_column(JSONB)
    highlights: Mapped[dict | None] = mapped_column(JSONB)
    faculty_contacts: Mapped[dict | None] = mapped_column(JSONB)
    cost_data: Mapped[dict | None] = mapped_column(JSONB)
    # Spec 23 §2.8 — promoted-placement categories this program opts into.
    # The actual promoted campaigns/auction live in Spec 25 (`promotions`); this
    # is just the program's declared participation set.
    promotion_categories: Mapped[list | None] = mapped_column(JSONB)
    # Spec 38 §2.2 — English-proficiency policy for international applicants.
    # Shape: {accepted_tests: [{test, min_score}], waiver_native_english_countries:
    # [iso2...], waiver_prior_degree_in_english: bool}. Distinct from the general
    # GRE/GMAT test policy in application_requirements (Spec 23 §3.3).
    english_policy: Mapped[dict | None] = mapped_column(JSONB)
    # Spec 06 §5.4 — bumped on any published-program edit so the rationale
    # cache (keyed by program_version) invalidates. Was a dead no-op before:
    # the column didn't exist and call sites read getattr(...,1) → always 1.
    feature_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    # Spec 46 §6 — fairness auto-halt. When disparate-impact Δ exceeds this
    # program's threshold for two consecutive weeks, the matching service stops
    # scoring NEW applicants for this cohort (existing scores remain). An
    # institution admin can lift the halt with a logged rationale (§6.3), which
    # sets fairness_override_active + override_expires_at; expiry re-arms the
    # halt on the next weekly compute.
    matching_halted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    fairness_override_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    override_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # §9 — tunable per program (default 0.20, range 0.05–0.40).
    fairness_threshold: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.20"), server_default="0.20"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="programs")
    school: Mapped[School | None] = relationship(back_populates="programs")


class IntakeRound(Base):
    __tablename__ = "intake_rounds"
    __table_args__ = (Index("ix_intake_rounds_program", "program_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    round_name: Mapped[str] = mapped_column(String(100), nullable=False)
    intake_term: Mapped[str | None] = mapped_column(String(50))
    application_open: Mapped[date | None] = mapped_column(Date)
    application_deadline: Mapped[date | None] = mapped_column(Date)
    decision_date: Mapped[date | None] = mapped_column(Date)
    program_start: Mapped[date | None] = mapped_column(Date)
    capacity: Mapped[int | None] = mapped_column(Integer)
    enrolled_count: Mapped[int] = mapped_column(Integer, default=0)
    requirements: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(20),
        default="upcoming",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ProgramChecklistItem(Base):
    __tablename__ = "program_checklist_items"
    __table_args__ = (Index("ix_prog_checklist_program", "program_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50),
        default="document",
        nullable=False,
    )
    requirement_level: Mapped[str] = mapped_column(
        String(20),
        default="required",
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TargetSegment(Base):
    __tablename__ = "target_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    segment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Spec 26 §7 — legacy flat AND criteria kept for campaign back-compat; the
    # nested include/exclude rule tree supersedes it when `rules` is set.
    criteria: Mapped[dict | None] = mapped_column(JSONB)
    rules: Mapped[dict | None] = mapped_column(JSONB)
    # Spec 26 §2.5 — uploaded prospect-list dataset ids merged into the audience.
    uploaded_list_ids: Mapped[list | None] = mapped_column(JSONB, default=list)
    # Spec 26 §5 — optional per-segment send cap (max sends per week).
    frequency_cap_per_week: Mapped[int | None] = mapped_column(Integer)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    # Spec 26 §7 — cached audience size from the last preview.
    preview_audience_count: Mapped[int | None] = mapped_column(Integer)
    preview_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="segments")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("target_segments.id", ondelete="SET NULL")
    )
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_type: Mapped[str | None] = mapped_column(String(30))
    message_subject: Mapped[str | None] = mapped_column(String(500))
    message_body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20))
    scheduled_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # ── Spec 25 §3 campaign setup ──────────────────────────────────────────
    objective: Mapped[str | None] = mapped_column(String(40))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    destination_type: Mapped[str | None] = mapped_column(String(40))
    destination_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    destination_url: Mapped[str | None] = mapped_column(String(1000))
    cta_type: Mapped[str | None] = mapped_column(String(30))
    # ['internal_messaging', 'external_email']
    channels: Mapped[list | None] = mapped_column(JSONB)
    # 0..N associated programs (Spec 25 §3 associate_program_ids)
    associate_program_ids: Mapped[list | None] = mapped_column(JSONB)
    associate_intake_round_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intake_rounds.id", ondelete="SET NULL")
    )
    # ── Spec 25 §3/§4 audience ─────────────────────────────────────────────
    audience_segment_ids: Mapped[list | None] = mapped_column(JSONB)
    audience_uploaded_list_ids: Mapped[list | None] = mapped_column(JSONB)
    audience_deduped_count: Mapped[int | None] = mapped_column(Integer)
    sent_count: Mapped[int | None] = mapped_column(Integer)
    # ── Spec 25 §7 approval workflow ───────────────────────────────────────
    submitted_for_approval_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="campaigns")
    recipients: Mapped[list[CampaignRecipient]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    links: Mapped[list[CampaignLink]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    actions: Mapped[list[CampaignAction]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignRecipient(Base):
    __tablename__ = "campaign_recipients"
    __table_args__ = (
        UniqueConstraint("campaign_id", "student_id"),
        Index("ix_campaign_recipients_campaign_email", "campaign_id", "email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    # Platform-student recipient (internal messaging + email). Nullable so an
    # uploaded-list contact (external email only) can be a recipient too.
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE")
    )
    uploaded_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_contacts.id", ondelete="SET NULL")
    )
    email: Mapped[str | None] = mapped_column(String(320))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    # 'internal' | 'external' — which channel this row was delivered through.
    channel: Mapped[str | None] = mapped_column(String(20))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bounced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(String(255))

    campaign: Mapped[Campaign] = relationship(back_populates="recipients")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(500))
    # Spec 20 §5 — revealed to RSVP'd students near start time.
    meeting_link: Mapped[str | None] = mapped_column(String(1000))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer)
    rsvp_count: Mapped[int] = mapped_column(Integer, default=0)
    # Spec 27 §5 — event impressions (feed/detail views) for the per-object
    # performance rollup.
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Spec 27 §3.2 lifecycle: draft | scheduled | live | completed | cancelled.
    status: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="events")
    rsvps: Mapped[list[EventRSVP]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class EventRSVP(Base):
    __tablename__ = "event_rsvps"
    __table_args__ = (UniqueConstraint("event_id", "student_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    # Spec 20 / 27 §3.1 — rsvp_status: registered | waitlisted | cancelled.
    rsvp_status: Mapped[str | None] = mapped_column(String(20))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    attended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Spec 27 §3.1 — attendance capture after the event: attended | no_show.
    # Null until the institution records attendance.
    attendance_status: Mapped[str | None] = mapped_column(String(20))

    event: Mapped[Event] = relationship(back_populates="rsvps")


class Reviewer(Base):
    __tablename__ = "reviewers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
    specializations: Mapped[dict | None] = mapped_column(JSONB)
    current_workload: Mapped[int] = mapped_column(Integer, default=0)
    max_workload: Mapped[int] = mapped_column(Integer, default=50)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="reviewers")


class InstitutionDataset(Base):
    __tablename__ = "institution_datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    row_count: Mapped[int | None] = mapped_column(Integer)
    column_mapping: Mapped[dict | None] = mapped_column(JSONB)
    normalization_map: Mapped[dict | None] = mapped_column(JSONB)
    validation_errors: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    usage_scope: Mapped[str | None] = mapped_column(String(50))
    coverage_start: Mapped[date | None] = mapped_column(Date)
    coverage_end: Mapped[date | None] = mapped_column(Date)
    version: Mapped[int] = mapped_column(Integer, default=1)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="datasets")
    versions: Mapped[list[DatasetVersion]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="DatasetVersion.version_number",
    )


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_number", name="uq_dataset_version_number"),
        Index("ix_dataset_versions_dataset", "dataset_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institution_datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer)
    changes_summary: Mapped[dict | None] = mapped_column(JSONB)
    validation_report: Mapped[dict | None] = mapped_column(JSONB)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    dataset: Mapped[InstitutionDataset] = relationship(back_populates="versions")


class DatasetMappingTemplate(Base):
    __tablename__ = "dataset_mapping_templates"
    __table_args__ = (
        UniqueConstraint("institution_id", "dataset_type", "name", name="uq_mapping_template_name"),
        Index("ix_mapping_templates_inst_type", "institution_id", "dataset_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    column_mapping: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class InstitutionPost(Base):
    __tablename__ = "institution_posts"
    __table_args__ = (Index("ix_institution_posts_inst_status", "institution_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[dict | None] = mapped_column(JSONB)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    tagged_program_ids: Mapped[dict | None] = mapped_column(JSONB)
    tagged_intake: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    template_name: Mapped[str | None] = mapped_column(String(255))
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    # Spec 27 §5 — per-object engagement counters. `view_count` above covers
    # impressions; these cover card/CTA clicks, saves, and the two downstream
    # conversions attributed to a post.
    click_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    save_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    request_info_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    apply_started_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Spec 27 §2.4 — CTAs attached to the post. List of
    # {type: view_program|rsvp|request_info|start_application|add_to_calendar,
    #  label: str, target: str}.
    ctas: Mapped[list | None] = mapped_column(JSONB)
    # Spec 27 §2.3 — visibility scope: {public: bool, segment_ids: [...],
    # region_scopes: [...]}. Null => public to followers (the default).
    visibility: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="posts")


class CampaignLink(Base):
    __tablename__ = "campaign_links"
    __table_args__ = (Index("ix_campaign_links_code", "short_code", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    destination_type: Mapped[str] = mapped_column(String(30), nullable=False)
    destination_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    custom_url: Mapped[str | None] = mapped_column(String(1000))
    short_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255))
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    campaign: Mapped[Campaign] = relationship(back_populates="links")


class CampaignAction(Base):
    __tablename__ = "campaign_actions"
    __table_args__ = (
        Index(
            "ix_campaign_actions_campaign_type",
            "campaign_id",
            "action_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaign_links.id", ondelete="SET NULL"),
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    campaign: Mapped[Campaign] = relationship(back_populates="actions")


class UploadedList(Base):
    """Spec 24/26 §2.5 — an institution's uploaded contact list (CSV import)
    usable as external-email audience for Campaigns. Each list owns N
    `UploadedContact` rows; merged with platform users by email at send time."""

    __tablename__ = "uploaded_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # 'csv_upload' | 'manual' | 'crm'. Tracked for source-consent compliance.
    source: Mapped[str] = mapped_column(String(30), nullable=False, server_default="csv_upload")
    source_consent_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institution_datasets.id", ondelete="SET NULL")
    )
    contact_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="uploaded_lists")
    contacts: Mapped[list[UploadedContact]] = relationship(
        back_populates="uploaded_list", cascade="all, delete-orphan"
    )


class UploadedContact(Base):
    __tablename__ = "uploaded_contacts"
    __table_args__ = (
        Index("ix_uploaded_contacts_list", "list_id"),
        Index("ix_uploaded_contacts_inst_email", "institution_id", "email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_lists.id", ondelete="CASCADE"), nullable=False
    )
    # Denormalized for institution-wide suppression lookups at send time.
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    extra: Mapped[dict | None] = mapped_column(JSONB)
    opted_out: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    opted_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    uploaded_list: Mapped[UploadedList] = relationship(back_populates="contacts")


class CampaignSuppression(Base):
    """Spec 25 §4 / 46 — institution-wide opt-out / suppression list. An email
    here is excluded from every external send (unsubscribe, bounce, complaint,
    or manual). Applied before the deduped audience count."""

    __tablename__ = "campaign_suppressions"
    __table_args__ = (
        UniqueConstraint("institution_id", "email", name="uq_campaign_suppression_inst_email"),
        Index("ix_campaign_suppressions_inst", "institution_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    # 'unsubscribed' | 'bounced' | 'complaint' | 'manual'
    reason: Mapped[str | None] = mapped_column(String(30))
    source_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="campaign_suppressions")


class Inquiry(Base):
    __tablename__ = "inquiries"
    __table_args__ = (Index("ix_inquiries_institution_status", "institution_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="SET NULL"),
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="SET NULL"),
    )
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    student_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    inquiry_type: Mapped[str] = mapped_column(
        String(30),
        default="general",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="new",
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    response_text: Mapped[str | None] = mapped_column(Text)
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    institution: Mapped[Institution] = relationship()
    program: Mapped[Program | None] = relationship()


class CommunicationTemplate(Base):
    __tablename__ = "communication_templates"
    __table_args__ = (
        Index(
            "ix_comm_templates_inst_type",
            "institution_id",
            "template_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="SET NULL"),
    )
    template_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSONB)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    institution: Mapped[Institution] = relationship()
    program: Mapped[Program | None] = relationship()


class Promotion(Base):
    __tablename__ = "promotions"
    __table_args__ = (Index("ix_promotions_active", "institution_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="SET NULL"),
    )
    promotion_type: Mapped[str] = mapped_column(
        String(30),
        default="spotlight",
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    targeting: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    impression_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    # Spec 27 §4.1 — promotion target: a program (default, uses program_id), the
    # institution overall, or a custom landing URL (target_url).
    target_kind: Mapped[str] = mapped_column(
        String(20), default="program", server_default="program", nullable=False
    )
    target_url: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    institution: Mapped[Institution] = relationship()
    program: Mapped[Program | None] = relationship()


class StudentProgramReview(Base):
    __tablename__ = "student_program_reviews"
    __table_args__ = (UniqueConstraint("student_id", "program_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # student_id is nullable because some reviews are ingested from
    # authoritative external sources (NYU Stories, Niche, bulletin). In that
    # case external_source holds the provenance and student_id stays null.
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating_teaching: Mapped[int | None] = mapped_column(Integer)
    rating_workload: Mapped[int | None] = mapped_column(Integer)
    rating_career_support: Mapped[int | None] = mapped_column(Integer)
    # Plan spec Insights dimensions (docs/Program Detail Page): we add
    # internship_access + community_culture to cover the 6-dimension rubric.
    rating_internship_access: Mapped[int | None] = mapped_column(Integer)
    rating_community_culture: Mapped[int | None] = mapped_column(Integer)
    rating_roi: Mapped[int | None] = mapped_column(Integer)
    rating_overall: Mapped[int | None] = mapped_column(Integer)
    review_text: Mapped[str | None] = mapped_column(Text)
    who_thrives_here: Mapped[str | None] = mapped_column(Text)
    reviewer_context: Mapped[dict | None] = mapped_column(JSONB)
    external_source: Mapped[dict | None] = mapped_column(JSONB)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class EmployerFeedback(Base):
    __tablename__ = "employer_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    rating_technical: Mapped[int | None] = mapped_column(Integer)
    rating_practical: Mapped[int | None] = mapped_column(Integer)
    rating_communication: Mapped[int | None] = mapped_column(Integer)
    # Plan spec Insights dimensions: add teamwork + reliability to cover the
    # 5-dimension employer rubric.
    rating_teamwork: Mapped[int | None] = mapped_column(Integer)
    rating_reliability: Mapped[int | None] = mapped_column(Integer)
    rating_overall: Mapped[int | None] = mapped_column(Integer)
    job_readiness_sentiment: Mapped[str | None] = mapped_column(
        String(20),
    )
    feedback_text: Mapped[str | None] = mapped_column(Text)
    hiring_pattern: Mapped[str | None] = mapped_column(String(255))
    feedback_year: Mapped[int | None] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
