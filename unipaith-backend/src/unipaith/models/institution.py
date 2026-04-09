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
    contact_email: Mapped[str | None] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(String(1000))
    website_url: Mapped[str | None] = mapped_column(String(1000))
    media_gallery: Mapped[dict | None] = mapped_column(JSONB)
    social_links: Mapped[dict | None] = mapped_column(JSONB)
    inquiry_routing: Mapped[dict | None] = mapped_column(JSONB)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
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
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_type: Mapped[str] = mapped_column(String(30), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="programs")


class IntakeRound(Base):
    __tablename__ = "intake_rounds"
    __table_args__ = (
        Index("ix_intake_rounds_program", "program_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
        String(20), default="upcoming", nullable=False,
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
    __table_args__ = (
        Index("ix_prog_checklist_program", "program_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), default="document", nullable=False,
    )
    requirement_level: Mapped[str] = mapped_column(
        String(20), default="required", nullable=False,
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
    criteria: Mapped[dict | None] = mapped_column(JSONB)
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
    __table_args__ = (UniqueConstraint("campaign_id", "student_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer)
    rsvp_count: Mapped[int] = mapped_column(Integer, default=0)
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
    rsvp_status: Mapped[str | None] = mapped_column(String(20))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    attended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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
    validation_errors: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    usage_scope: Mapped[str | None] = mapped_column(String(50))
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


class InstitutionPost(Base):
    __tablename__ = "institution_posts"
    __table_args__ = (
        Index("ix_institution_posts_inst_status", "institution_id", "status"),
    )

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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship(back_populates="posts")


class CampaignLink(Base):
    __tablename__ = "campaign_links"
    __table_args__ = (
        Index("ix_campaign_links_code", "short_code", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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


class Inquiry(Base):
    __tablename__ = "inquiries"
    __table_args__ = (
        Index("ix_inquiries_institution_status", "institution_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
        String(30), default="general", nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="new", nullable=False,
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

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
        String(30), nullable=False,
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
    __table_args__ = (
        Index("ix_promotions_active", "institution_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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
        String(30), default="spotlight", nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    targeting: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False,
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    impression_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
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
    __table_args__ = (
        UniqueConstraint("student_id", "program_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
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
    rating_roi: Mapped[int | None] = mapped_column(Integer)
    rating_overall: Mapped[int | None] = mapped_column(Integer)
    review_text: Mapped[str | None] = mapped_column(Text)
    who_thrives_here: Mapped[str | None] = mapped_column(Text)
    reviewer_context: Mapped[dict | None] = mapped_column(JSONB)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
