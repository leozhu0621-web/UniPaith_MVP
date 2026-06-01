"""Spec 40 — Recruitment CRM (Pre-Applicant) models.

The institution top-of-funnel: prospects *before* they become applicants, the
recruiter travel calendar, the HS / college-fair directory, and territory
management. Sits upstream of the applicant pipeline (``31``) and the marketing
surfaces (campaigns ``25``, segments ``26``, events ``27``).

Design notes:
- Every row is institution-scoped (``institution_id`` FK, CASCADE).
- ``Prospect`` carries an explicit ``converted_application_id`` forward link so a
  converted prospect never spawns a duplicate person record (§2.1 / §9).
- ``consent_outreach`` defaults ``False`` — marketing outreach is opt-in only
  (§7 / spec ``46``). It is surfaced on every prospect in the UI.
- Territory counts / conversion rates are computed aggregate-on-read in the
  service (mirrors ``yield_service.py``); only durable config lives here.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Canonical enums (kept in sync with the migration CHECK constraints + the
# Pydantic schemas in ``schemas/recruitment.py``).
PROSPECT_SOURCES = ("fair", "list", "inquiry", "referral", "web", "visit")
PROSPECT_STAGES = ("suspect", "prospect", "engaged", "inquiry", "applicant")
TRIP_STATUSES = ("planned", "active", "done", "cancelled")
VISIT_KINDS = ("school", "fair")
VISIT_STATUSES = ("planned", "confirmed", "done")
FAIR_KINDS = ("fair", "high_school")
FAIR_STATUSES = ("prospective", "registered", "confirmed", "attended", "skipped")


class Prospect(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prospects"
    __table_args__ = (
        CheckConstraint(
            "source IN ('fair','list','inquiry','referral','web','visit')",
            name="ck_prospects_source",
        ),
        CheckConstraint(
            "stage IN ('suspect','prospect','engaged','inquiry','applicant')",
            name="ck_prospects_stage",
        ),
        Index("ix_prospects_inst_stage", "institution_id", "stage"),
        Index("ix_prospects_inst_source", "institution_id", "source"),
        Index("ix_prospects_inst_territory", "institution_id", "territory_id"),
        Index("ix_prospects_inst_owner", "institution_id", "owner_user_id"),
        # Lookup index used by the import dedup path (lower(email) compared in
        # the service). Non-unique: email is nullable and dedup is per-import.
        Index("ix_prospects_inst_email", "institution_id", "email"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))

    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(100))

    # Program areas / interests (list[str]).
    interests: Mapped[list | None] = mapped_column(JSONB)

    source: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    # Free-text provenance detail, e.g. the fair name or purchased-list name.
    source_detail: Mapped[str | None] = mapped_column(String(255))
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="prospect")

    territory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("territories.id", ondelete="SET NULL")
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    owner_name: Mapped[str | None] = mapped_column(String(255))

    # Forward link once the prospect starts an application (§2.1). Idempotent —
    # set once, never spawns a second person record.
    converted_application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL")
    )

    # Marketing-outreach consent (§7 / 46). Opt-in only.
    consent_outreach: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )

    # AI (ProspectPrioritizer §5) — apply-likelihood 0..1 + a short reason.
    apply_likelihood: Mapped[float | None] = mapped_column(Float)
    priority_reason: Mapped[str | None] = mapped_column(Text)

    notes: Mapped[str | None] = mapped_column(Text)


class RecruitmentTrip(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recruitment_trips"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned','active','done','cancelled')",
            name="ck_recruitment_trips_status",
        ),
        Index("ix_recruitment_trips_inst_start", "institution_id", "start_date"),
        Index("ix_recruitment_trips_recruiter", "institution_id", "recruiter_user_id"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str | None] = mapped_column(String(120))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    recruiter_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    recruiter_name: Mapped[str | None] = mapped_column(String(255))

    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    spend: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")
    notes: Mapped[str | None] = mapped_column(Text)

    visits: Mapped[list[TripVisit]] = relationship(
        "TripVisit",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripVisit.visit_date",
    )


class TripVisit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "trip_visits"
    __table_args__ = (
        CheckConstraint("kind IN ('school','fair')", name="ck_trip_visits_kind"),
        CheckConstraint("status IN ('planned','confirmed','done')", name="ck_trip_visits_status"),
        Index("ix_trip_visits_trip", "trip_id"),
    )

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recruitment_trips.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="school")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fair_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recruitment_fairs.id", ondelete="SET NULL")
    )
    visit_date: Mapped[date | None] = mapped_column(Date)
    prospects_met: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="planned")
    notes: Mapped[str | None] = mapped_column(Text)

    trip: Mapped[RecruitmentTrip] = relationship("RecruitmentTrip", back_populates="visits")


class RecruitmentFair(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recruitment_fairs"
    __table_args__ = (
        CheckConstraint("kind IN ('fair','high_school')", name="ck_recruitment_fairs_kind"),
        CheckConstraint(
            "status IN ('prospective','registered','confirmed','attended','skipped')",
            name="ck_recruitment_fairs_status",
        ),
        Index("ix_recruitment_fairs_inst", "institution_id"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(12), nullable=False, default="fair")

    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(100))

    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(255))

    # Prior-year yield from this source — drives the TerritoryOptimizer ranking.
    prior_year_yield: Mapped[int | None] = mapped_column(Integer)

    event_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(14), nullable=False, default="prospective")
    notes: Mapped[str | None] = mapped_column(Text)


class Territory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "territories"
    __table_args__ = (Index("ix_territories_inst", "institution_id"),)

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # { "regions": [...], "countries": [...], "cities": [...] } — used for the
    # coverage view and (later) auto-assignment of prospects to a territory.
    geo: Mapped[dict | None] = mapped_column(JSONB)

    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    owner_name: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
