"""Spec 60 §5 — the world-reference tables (the clean projection).

``knowledge_documents`` / ``knowledge_links`` stay the raw graph; these are the
typed, normalized, provenance-carrying projection the consuming surfaces read
(§5.2). Each row is provisional + source-cited + confidence-scored (the
``ProvenanceMixin``), so a number on a student surface can always answer "sourced
from <domain>, updated N days ago" (§4). Verified first-party data always wins
(§8); these reference facts are shown as "typical for this field," distinct from
a program's own claim.

Typed tables for the hot domains (§3.1–§3.6); ``reference_entities`` is the
generic long-tail. ``scholarships`` (§5.1) feeds the aid-likelihood band + net
price (09 / 11).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from unipaith.models.crawler import (
    KNOWLEDGE_SOURCE_CHECK,
    KNOWLEDGE_STATUS_CHECK,
    ProvenanceMixin,
)


class Scholarship(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§5.1 — institution/program-linked or external scholarships. Feeds the
    ``aid_scholarship_likelihood_band`` + net-price (09 / 11). ``institution_id`` /
    ``program_id`` are soft references (a row may be a purely external award)."""

    __tablename__ = "scholarships"

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    scholarship_type: Mapped[str] = mapped_column(String(24), nullable=False, default="external")
    institution_id: Mapped[UUID | None] = mapped_column()
    program_id: Mapped[UUID | None] = mapped_column()
    sponsor: Mapped[str | None] = mapped_column(String(300))
    amount_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    amount_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_renewable: Mapped[bool | None] = mapped_column()
    eligibility: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    deadline: Mapped[date | None] = mapped_column(Date)
    application_url: Mapped[str | None] = mapped_column(Text)
    distribution_history: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint(
            "scholarship_type IN ('merit','need','external','institutional','departmental')",
            name="ck_scholarships_type",
        ),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_scholarships_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_scholarships_status"),
        Index("ix_scholarships_institution", "institution_id"),
        Index("ix_scholarships_program", "program_id"),
        Index("ix_scholarships_type", "scholarship_type"),
    )


class RefOccupation(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§3.1 — careers/occupations (BLS, O*NET). Feeds career-alignment + the
    outcome preview. Keyed on the SOC code."""

    __tablename__ = "ref_occupations"

    soc_code: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    median_salary: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    employment: Mapped[int | None] = mapped_column(Integer)
    projected_growth_pct: Mapped[float | None] = mapped_column(Float)
    outlook: Mapped[str | None] = mapped_column(String(40))
    education_typical: Mapped[str | None] = mapped_column(String(120))
    related_majors: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    __table_args__ = (
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_ref_occupations_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_ref_occupations_status"),
        Index("ix_ref_occupations_title", "title"),
    )


class RefTest(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§3.2 — standardized tests (ETS / College Board / ACT / British Council).
    Feeds test compatibility / superscore. Keyed on a stable test code."""

    __tablename__ = "ref_tests"

    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False, default="other")
    sections: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    score_min: Mapped[float | None] = mapped_column(Float)
    score_max: Mapped[float | None] = mapped_column(Float)
    validity_years: Mapped[int | None] = mapped_column(Integer)
    superscore_allowed: Mapped[bool | None] = mapped_column()

    __table_args__ = (
        CheckConstraint(
            "category IN ('english','graduate','undergraduate','subject','other')",
            name="ck_ref_tests_category",
        ),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_ref_tests_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_ref_tests_status"),
    )


class RefVisa(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§3.3 — visa & immigration (USCIS / IRCC / UKVI). Feeds the visa feasibility
    band (42 §4.3) and serves spec 38. Keyed on (country, code)."""

    __tablename__ = "ref_visas"

    country: Mapped[str] = mapped_column(String(60), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    requirements: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    work_rights: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    duration: Mapped[str | None] = mapped_column(String(120))
    financial_proof_required: Mapped[bool | None] = mapped_column()

    __table_args__ = (
        UniqueConstraint("country", "code", name="uq_ref_visas_country_code"),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_ref_visas_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_ref_visas_status"),
        Index("ix_ref_visas_country", "country"),
    )


class RefGeoCost(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§3.4 — cost of living & geography. Feeds net-cost / affordability. Keyed on
    (country, locale)."""

    __tablename__ = "ref_geo_cost"

    locale: Mapped[str] = mapped_column(String(160), nullable=False)
    country: Mapped[str] = mapped_column(String(60), nullable=False)
    cost_of_living_index: Mapped[float | None] = mapped_column(Float)
    rent_index: Mapped[float | None] = mapped_column(Float)
    monthly_estimate: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    __table_args__ = (
        UniqueConstraint("country", "locale", name="uq_ref_geo_cost_country_locale"),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_ref_geo_cost_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_ref_geo_cost_status"),
    )


class RefMajor(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§3.5 — majors / curriculum (CIP, catalogs). Feeds major-track fit + prereq
    gaps. Keyed on the CIP code."""

    __tablename__ = "ref_majors"

    cip_code: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    typical_curriculum: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    prerequisites: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    related_occupations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    __table_args__ = (
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_ref_majors_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_ref_majors_status"),
        Index("ix_ref_majors_title", "title"),
    )


class RefRanking(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§3.6 — rankings. Shown as "reported by <ranker>, <year>", never as fact."""

    __tablename__ = "ref_rankings"

    ranker: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(300), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(24), nullable=False, default="institution")
    scope: Mapped[str | None] = mapped_column(String(120))
    rank: Mapped[int | None] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ranker", "entity_name", "scope", "year", name="uq_ref_rankings_subject_year"
        ),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_ref_rankings_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_ref_rankings_status"),
        Index("ix_ref_rankings_entity", "entity_name"),
    )


class RefAccreditation(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§3.6 — accreditation status by body + entity."""

    __tablename__ = "ref_accreditation"

    body: Mapped[str] = mapped_column(String(200), nullable=False)
    body_type: Mapped[str] = mapped_column(String(24), nullable=False, default="regional")
    entity_name: Mapped[str] = mapped_column(String(300), nullable=False)
    accreditation_status: Mapped[str | None] = mapped_column(String(60))
    scope: Mapped[str | None] = mapped_column(String(200))
    valid_through: Mapped[date | None] = mapped_column(Date)

    __table_args__ = (
        UniqueConstraint("body", "entity_name", "scope", name="uq_ref_accreditation_body_entity"),
        CheckConstraint(
            "body_type IN ('regional','national','programmatic')",
            name="ck_ref_accreditation_body_type",
        ),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_ref_accreditation_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_ref_accreditation_status"),
        Index("ix_ref_accreditation_entity", "entity_name"),
    )


class ReferenceEntity(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§5.2 — the generic long-tail. Domains that don't (yet) warrant a typed
    table (grading scales, language equivalency, competitions, deadlines…) land
    here as ``(ref_type, ref_key) → data`` JSONB, still provenance-carrying."""

    __tablename__ = "reference_entities"

    ref_type: Mapped[str] = mapped_column(String(60), nullable=False)
    ref_key: Mapped[str] = mapped_column(String(160), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("ref_type", "ref_key", name="uq_reference_entities_type_key"),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_reference_entities_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_reference_entities_status"),
        Index("ix_reference_entities_type", "ref_type"),
    )
