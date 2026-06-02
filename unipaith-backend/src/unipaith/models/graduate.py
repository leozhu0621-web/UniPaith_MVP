"""Spec 41 — Graduate & PhD Admissions models.

The graduate-specific admissions layer that sits *on top of* the shared pipeline
(``31`` intake, ``32`` review, ``34`` offers, ``35`` yield) rather than forking
it. Graduate admissions is faculty-driven and funding-centric:

- **Faculty-advisor matching** (``faculty_profiles`` + ``advisor_matches``):
  research-interest alignment between applicants and advisors, both directions,
  with mutual-interest flags surfaced to the department (§2.1).
- **Research-interest alignment** (``graduate_intents``): the applicant's stated
  research interests + target advisors + statement of purpose; the SoP is parsed
  into interest tags by ``SoPInterestExtractor`` (§2.2 / ``45``).
- **Funding-package builder** (``funding_pools`` + ``funding_packages`` +
  ``funding_package_components``): a TA/RA/fellowship/waiver/stipend package built
  against per-source budget pools that cannot be over-committed (§2.3).
- **Department review portal** (``departments`` + ``department_reviews``):
  departments run a scoped review and *recommend*; central office *confirms /
  releases* (§2.4) — a two-stage, role-gated flow.

Design notes:
- Every durable row is institution- or application-scoped (FK CASCADE), mirroring
  ``recruitment.py``. Aggregate metrics (funding committed-vs-budget, department
  pool/yield counts) are computed aggregate-on-read in ``graduate_service.py``.
- Grad-only features are gated on the program ``degree_type`` (§6) — see
  ``graduate_service.is_graduate_degree``; nothing here is visible for an
  undergrad program.
- A finalized ``FundingPackage`` is mirrored into the existing
  ``OfferLetter.assistantship_details`` / ``financial_package_total`` so the
  student offer view (Spec 18) renders the package with no student-side schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Canonical enums — kept in sync with the migration CHECK constraints and the
# Pydantic schemas in ``api/graduate.py``.
FUNDING_POOL_KINDS = ("department", "grant", "fellowship", "other")
FUNDING_COMPONENT_KINDS = ("TA", "RA", "fellowship", "tuition_waiver", "stipend")
FUNDING_PACKAGE_STATUSES = ("draft", "proposed", "finalized", "rescinded")
# Aligns with the Spec 34 decision vocabulary so a confirmed recommendation maps
# straight onto ``MakeDecisionService.release_decision``.
RECOMMENDED_DECISIONS = ("admitted", "conditional_admission", "waitlisted", "rejected", "deferred")
CENTRAL_STATUSES = ("pending", "confirmed", "overridden")


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A reviewing department within an institution (§2.4).

    Departments anchor the scoped review portal (``/i/departments/:deptId``),
    the faculty roster, and the funding pools. ``programs.department_id`` links a
    program to its department (the legacy free-text ``programs.department`` stays
    for back-compat).
    """

    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("institution_id", "name", name="uq_departments_inst_name"),
        Index("ix_departments_inst", "institution_id"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class FacultyProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A faculty advisor — the matching counterpart to an applicant (§2.1 / §4).

    ``user_id`` is nullable: a faculty row can exist before the faculty sub-role
    login is wired (Spec §8 — Phase-2 auth). When set, that user (role
    ``faculty``) is scoped to this department.
    """

    __tablename__ = "faculty_profiles"
    __table_args__ = (
        Index("ix_faculty_profiles_inst", "institution_id"),
        Index("ix_faculty_profiles_dept", "department_id"),
        Index("ix_faculty_profiles_user", "user_id"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    # Structured research areas (list[str]) — the embedding/overlap signal.
    research_areas: Mapped[list | None] = mapped_column(JSONB)
    accepting_students: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    openings: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    funding_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    bio: Mapped[str | None] = mapped_column(Text)
    homepage_url: Mapped[str | None] = mapped_column(String(1000))


class GraduateIntent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The applicant's grad-specific intent: research interests + target advisors
    + statement of purpose (§2.1 / §2.2, extends ``42`` §3.12).

    One row per application. ``extracted_interests`` / ``alignment_summary`` are
    written by ``SoPInterestExtractor`` (§5); ``research_interests`` is the
    applicant's own stated list.
    """

    __tablename__ = "graduate_intents"
    __table_args__ = (UniqueConstraint("application_id", name="uq_graduate_intents_app"),)

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    research_interests: Mapped[list | None] = mapped_column(JSONB)
    target_advisor_ids: Mapped[list | None] = mapped_column(JSONB)
    target_advisor_names: Mapped[list | None] = mapped_column(JSONB)
    statement_of_purpose: Mapped[str | None] = mapped_column(Text)
    funding_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    # AI (SoPInterestExtractor §5) — parsed interest tags + a short summary.
    extracted_interests: Mapped[list | None] = mapped_column(JSONB)
    alignment_summary: Mapped[str | None] = mapped_column(Text)


class AdvisorMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A ranked (applicant, advisor) research-fit row (§2.1 / §4).

    ``alignment_score`` (0-100) is recomputed deterministically from
    research-interest overlap on each list call; the two interest booleans are
    stateful (applicant naming the advisor, the advisor flagging interest) and
    ``mutual`` is their AND, surfaced to the department.
    """

    __tablename__ = "advisor_matches"
    __table_args__ = (
        UniqueConstraint("application_id", "faculty_id", name="uq_advisor_match_app_faculty"),
        Index("ix_advisor_matches_app", "application_id"),
        Index("ix_advisor_matches_faculty", "faculty_id"),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    faculty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("faculty_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    alignment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    applicant_named_advisor: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    advisor_flagged_interest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    mutual: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    rationale: Mapped[str | None] = mapped_column(Text)


class FundingPool(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A per-source funding budget (department / grant / fellowship) (§2.3).

    Self-contained accounting (Spec §11): the ``committed`` amount is summed
    aggregate-on-read from finalized + proposed package components; this row only
    holds the durable ``total_budget``.
    """

    __tablename__ = "funding_pools"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('department','grant','fellowship','other')",
            name="ck_funding_pools_kind",
        ),
        Index("ix_funding_pools_inst", "institution_id"),
        Index("ix_funding_pools_dept", "department_id"),
    )

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="department")
    total_budget: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0", default=0
    )
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="USD")
    notes: Mapped[str | None] = mapped_column(Text)


class FundingPackage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A funding offer built for one application (§2.3 / §4).

    One row per application. Becomes part of the offer (Spec 34) when finalized;
    the multi-year mix is modeled by the per-component ``years`` arrays.
    """

    __tablename__ = "funding_packages"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_funding_packages_app"),
        CheckConstraint(
            "status IN ('draft','proposed','finalized','rescinded')",
            name="ck_funding_packages_status",
        ),
        Index("ix_funding_packages_dept", "department_id"),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0", default=0
    )
    currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="USD")
    multi_year: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    proposed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    components: Mapped[list[FundingPackageComponent]] = relationship(
        "FundingPackageComponent",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="FundingPackageComponent.created_at",
    )


class FundingPackageComponent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One line of a funding package: a TA/RA/fellowship/waiver/stipend amount
    drawn from a source pool over one or more years (§4)."""

    __tablename__ = "funding_package_components"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('TA','RA','fellowship','tuition_waiver','stipend')",
            name="ck_funding_components_kind",
        ),
        Index("ix_funding_components_package", "package_id"),
        Index("ix_funding_components_pool", "source_pool_id"),
    )

    package_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("funding_packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, server_default="0", default=0
    )
    source_pool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funding_pools.id", ondelete="SET NULL")
    )
    # Years this component applies to, e.g. [1] or [2, 3, 4] (§3.4 multi-year).
    years: Mapped[list | None] = mapped_column(JSONB)
    label: Mapped[str | None] = mapped_column(String(255))

    package: Mapped[FundingPackage] = relationship("FundingPackage", back_populates="components")


class DepartmentReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """The two-stage release record for one application (§2.4 / §6).

    Department *recommends* (sets ``recommended_decision`` + ``central_status =
    'pending'``); central office *confirms* (``central_status = 'confirmed'`` →
    calls the Spec 34 release path) or *overrides* (``'overridden'``). Faculty /
    department may recommend; only central may release (role-gated).
    """

    __tablename__ = "department_reviews"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_department_reviews_app"),
        CheckConstraint(
            "central_status IS NULL OR central_status IN ('pending','confirmed','overridden')",
            name="ck_department_reviews_central_status",
        ),
        Index("ix_department_reviews_dept", "department_id"),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )
    recommended_decision: Mapped[str | None] = mapped_column(String(30))
    recommended_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    recommended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    committee_notes: Mapped[str | None] = mapped_column(Text)
    funding_package_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funding_packages.id", ondelete="SET NULL")
    )
    central_status: Mapped[str | None] = mapped_column(String(20))
    central_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    central_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    central_decision: Mapped[str | None] = mapped_column(String(30))
