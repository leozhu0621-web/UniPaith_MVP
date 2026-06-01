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
    # 30 chars to fit the spec-34 decision vocabulary (e.g. ``conditional_admission``).
    decision: Mapped[str | None] = mapped_column(String(30))
    decision_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviewers.id", ondelete="SET NULL")
    )
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_notes: Mapped[str | None] = mapped_column(Text)
    completeness_status: Mapped[str | None] = mapped_column(String(30))
    missing_items: Mapped[dict | None] = mapped_column(JSONB)
    # --- Spec 15 · Applications workspace ---
    # internal = submit through UniPaith; external = student submits on the
    # institution's own portal and tracks progress here (spec 15 §7).
    submission_mode: Mapped[str] = mapped_column(
        String(20), server_default="internal", nullable=False
    )
    readiness_pct: Mapped[int | None] = mapped_column(Integer)
    # Guardrails against low-fit / mass applications (spec 15 §6.5 / §8, G-S4).
    intent_picker: Mapped[str | None] = mapped_column(String(30))
    intent_rationale: Mapped[str | None] = mapped_column(Text)
    fit_band: Mapped[str | None] = mapped_column(String(10))
    guardrail_blockers: Mapped[list | None] = mapped_column(JSONB)
    # --- Spec 18 · Decisions & Offers ---
    # Student-side outcome action, distinct from the institution `decision`
    # above: one of accepted_by_student | declined_by_student | withdrawn.
    student_decision: Mapped[str | None] = mapped_column(String(24))
    # --- Spec 35 · Waitlist movement (§3.3) ---
    # Rank within a program's waitlist (1 = next to be offered). Set when the
    # reviewer waitlists; ``offer-next`` promotes the lowest rank first.
    waitlist_rank: Mapped[int | None] = mapped_column(Integer)
    waitlisted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    program: Mapped[Program] = relationship("Program", lazy="noload")  # type: ignore[name-defined]  # noqa: F821


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
    # Spec 33 §6 — interviewing rubric is distinct from the application rubric.
    # 'application' (default, back-compat) | 'interview'.
    rubric_kind: Mapped[str] = mapped_column(
        String(20), server_default="application", nullable=False
    )
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
    # Spec 33 §2 interview types: live / recorded_async / portfolio_review /
    # technical_assessment / third_party_platform (legacy video/phone/in_person
    # values still render — see calendar_service kind sets).
    interview_type: Mapped[str | None] = mapped_column(String(30))
    proposed_times: Mapped[dict | None] = mapped_column(JSONB)
    confirmed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location_or_link: Mapped[str | None] = mapped_column(String(500))
    # Spec 33 §7 status: proposed / confirmed / completed / cancelled / no_show.
    status: Mapped[str | None] = mapped_column(String(20))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    # Spec 33 §5/§7 — async (recorded_async / technical_assessment) submission
    # window; when past with no recording the response renders "No submission
    # received" (§8) and review may advance without the interview.
    async_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recording_url: Mapped[str | None] = mapped_column(String(1000))
    # Denormalized latest recommendation (recommend / neutral / not_recommend)
    # mirrored from the most recent InterviewScore so the list/table avoids an
    # extra join (§4 KPI table). Authoritative scores live on interview_scores.
    recommendation: Mapped[str | None] = mapped_column(String(20))
    # Invite notes for the student (§5) — also mirrored into the Inbox message body.
    notes_to_student: Mapped[str | None] = mapped_column(Text)
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
    # Spec 33 §7 — scores[] carries a created_at so the review packet can order
    # multiple interviewer scores chronologically.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


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
    # --- Spec 18 · Decisions & Offers (student-facing offer shape) ---
    # Same Offer row whether platform-issued (internal) or recorded by the
    # student after an off-platform decision (received_externally=True, §14).
    received_externally: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    decision_date: Mapped[date | None] = mapped_column(Date)
    scholarship_currency: Mapped[str | None] = mapped_column(String(8))
    tuition_estimate: Mapped[int | None] = mapped_column(Integer)
    total_cost_estimate: Mapped[int | None] = mapped_column(Integer)
    start_term_season: Mapped[str | None] = mapped_column(String(16))
    start_term_year: Mapped[int | None] = mapped_column(Integer)
    # [{action, by_date}] next-step actions surfaced in the per-offer UX (§4).
    next_step_actions: Mapped[list | None] = mapped_column(JSONB)
    # Cached OutcomeBriefForOfferLetter output (45 §15): structured
    # {key_terms, deadlines, next_steps, summary}. Falls back to rule-based.
    plain_language_brief: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EnrollmentRecord(Base):
    """Spec 35 — Enrollment confirmation & yield state machine (per offer).

    Extends the original thin record (kept ``enrolled_at`` / ``enrollment_status``
    / ``start_term`` for the D2 confidence-outcome hook back-compat) with the
    §5 state machine: ``accepted → intent_confirmed → deposit_recorded →
    enrollment_confirmed → enrolled`` (↘ ``withdrew`` / ``deferred``). Deposit is
    **status-only** in MVP (Spec 39 owns real collection)."""

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
    # The offer this enrollment confirms against (spec 35 §5). Nullable so the
    # legacy D2 outcome path (which created bare rows) still validates.
    offer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("offer_letters.id", ondelete="SET NULL")
    )
    # §5 state machine. Defaults to ``accepted`` — the row is born when the
    # student accepts the offer.
    state: Mapped[str] = mapped_column(String(24), server_default="accepted", nullable=False)
    # Deposit is status-only in MVP (paid/waived/pending/none); §1 scope boundary.
    deposit_status: Mapped[str] = mapped_column(String(10), server_default="none", nullable=False)
    deposit_amount: Mapped[int | None] = mapped_column(Integer)
    intent_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrollment_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decline_reason: Mapped[str | None] = mapped_column(Text)
    # {requested: bool, to_term: {season, year} | null, approved: bool} (§2.2/§3.1).
    deferral: Mapped[dict | None] = mapped_column(JSONB)
    # [{item, status: pending|complete|overdue|waived, due: ISO|null, consequence}] (§2.1).
    checklist: Mapped[list | None] = mapped_column(JSONB)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    enrollment_status: Mapped[str | None] = mapped_column(String(20))
    start_term: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AIPacketSummary(Base):
    __tablename__ = "ai_packet_summaries"
    __table_args__ = (UniqueConstraint("application_id", name="uq_ai_packet_app"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
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

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
        String(20),
        default="medium",
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    # Spec 31 §6 — resolution outcome chosen by the reviewer:
    # acceptable | requires_clarification | reject_application.
    resolution: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
