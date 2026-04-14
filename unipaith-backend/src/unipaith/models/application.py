from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
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


class HistoricalOutcome(Base):
    __tablename__ = "historical_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    applicant_profile_summary: Mapped[dict | None] = mapped_column(JSONB)
    outcome: Mapped[str | None] = mapped_column(String(20))
    enrolled: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("student_id", "program_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    status: Mapped[str | None] = mapped_column(String(30))
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    match_reasoning_text: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision: Mapped[str | None] = mapped_column(String(20))
    decision_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewers.id", ondelete="SET NULL")
    )
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_notes: Mapped[str | None] = mapped_column(Text)
    completeness_status: Mapped[str | None] = mapped_column(String(30))
    missing_items: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    program: Mapped[Program] = relationship("Program", lazy="selectin")  # type: ignore[name-defined]  # noqa: F821


class ApplicationChecklist(Base):
    __tablename__ = "application_checklists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    items: Mapped[dict | None] = mapped_column(JSONB)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    auto_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApplicationSubmission(Base):
    __tablename__ = "application_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    submitted_documents: Mapped[dict | None] = mapped_column(JSONB)
    submission_package_url: Mapped[str | None] = mapped_column(String(1000))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmation_number: Mapped[str | None] = mapped_column(String(20), unique=True)


class ReviewAssignment(Base):
    __tablename__ = "review_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewers.id", ondelete="CASCADE"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20))


class Rubric(Base):
    __tablename__ = "rubrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL")
    )
    rubric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    criteria: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ApplicationScore(Base):
    __tablename__ = "application_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewers.id", ondelete="CASCADE"), nullable=False
    )
    rubric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False
    )
    criterion_scores: Mapped[dict | None] = mapped_column(JSONB)
    total_weighted_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    scored_by_type: Mapped[str | None] = mapped_column(String(20))
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewers.id", ondelete="CASCADE"), nullable=False
    )
    interview_type: Mapped[str | None] = mapped_column(String(20))
    proposed_times: Mapped[dict | None] = mapped_column(JSONB)
    confirmed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location_or_link: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str | None] = mapped_column(String(20))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class InterviewScore(Base):
    __tablename__ = "interview_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewers.id", ondelete="CASCADE"), nullable=False
    )
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubrics.id", ondelete="SET NULL")
    )
    criterion_scores: Mapped[dict | None] = mapped_column(JSONB)
    total_weighted_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    interviewer_notes: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(String(20))


class OfferLetter(Base):
    __tablename__ = "offer_letters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    offer_type: Mapped[str | None] = mapped_column(String(30))
    tuition_amount: Mapped[int | None] = mapped_column(Integer)
    scholarship_amount: Mapped[int] = mapped_column(Integer, default=0)
    assistantship_details: Mapped[dict | None] = mapped_column(JSONB)
    financial_package_total: Mapped[int | None] = mapped_column(Integer)
    conditions: Mapped[dict | None] = mapped_column(JSONB)
    response_deadline: Mapped[date | None] = mapped_column(Date)
    generated_letter_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str | None] = mapped_column(String(20))
    student_response: Mapped[str | None] = mapped_column(String(20))
    response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decline_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EnrollmentRecord(Base):
    __tablename__ = "enrollment_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    enrollment_status: Mapped[str | None] = mapped_column(String(20))
    start_term: Mapped[str | None] = mapped_column(String(20))


class AIPacketSummary(Base):
    __tablename__ = "ai_packet_summaries"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_ai_packet_app"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rubrics.id", ondelete="SET NULL"),
    )
    overall_summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[dict | None] = mapped_column(JSONB)
    concerns: Mapped[dict | None] = mapped_column(JSONB)
    criterion_assessments: Mapped[dict | None] = mapped_column(JSONB)
    recommended_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    confidence_level: Mapped[str | None] = mapped_column(String(20))
    model_used: Mapped[str | None] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
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


class IntegritySignal(Base):
    __tablename__ = "integrity_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False,
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
