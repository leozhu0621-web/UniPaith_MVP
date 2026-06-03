"""Spec 68 — Outcomes & Admissions-History Data Layer (typed, not JSONB).

Replaces the untyped ``Program.outcomes_data`` / ``Program.cost_data`` JSONB
blobs and the fabricated per-applicant ``HistoricalOutcome`` rows with a typed,
time-windowed, provenance-carrying data layer that every consumer reads through
``services/outcomes_service`` instead of digging into JSON by string key.

- ``ProgramOutcome`` / ``SchoolOutcome`` — one row per (target, metric, window,
  source). ``metric`` is a closed enum (§2); the value is a scalar
  (``value_numeric``) or a structured payload (``value_json`` — bands, geography).
  Absence is first-class: a program with no employer data has *no row*, never a
  zero (§2). Every fact carries a required ``reference_period`` window (§2) and
  the provenance envelope (``ProvenanceMixin``).
- ``ProgramTopEmployer`` — top hiring employers by count/recency (§2): a list,
  not a scalar, so it gets its own child table.
- ``ProgramAdmissionsHistory`` / ``SchoolAdmissionsHistory`` — aggregate admit
  stats per cycle (§3). ``class_profile`` carries **academic aggregates only**
  (``ALLOWED_CLASS_PROFILE_KEYS``); no protected/proxy attribute may enter,
  because ``67`` reads it as a training feature (§3 / spec 46 §6).
- ``ReviewThemeSummary`` — the top-of-Insights theme block synthesised over the
  existing ``student_program_reviews`` / ``employer_feedback`` tables (§5); the
  review tables themselves are unchanged.

Authority (§7, first-party-wins): outcomes have their own source vocabulary
because, unlike the crawler's reference graph (``KNOWLEDGE_SOURCES``, where
``seed`` is lowest), licensed government data (IPEDS / College Scorecard) is
*high* trust for outcomes — it outranks a crawl. Order: ``crawled`` < ``licensed``
< ``reported`` (institution-reported partner data wins, §7).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from unipaith.models.crawler import KNOWLEDGE_STATUS_CHECK, ProvenanceMixin

# ── Source authority (§7) — outcomes-specific, ascending trust ──────────────
# Distinct from crawler.KNOWLEDGE_SOURCES: for outcomes, licensed government
# data is authoritative, so it sits *above* a crawl. Institution-reported
# (partner DPA) wins (first-party-wins, §7).
OUTCOME_SOURCES = ("crawled", "licensed", "reported")
OUTCOME_SOURCE_CHECK = "source IN ('crawled','licensed','reported')"
OUTCOME_SOURCE_AUTHORITY: dict[str, int] = {"crawled": 1, "licensed": 2, "reported": 3}

# ── The closed metric vocabulary (§2 — Business Methodology:121-128) ─────────
# Scalars live in value_numeric; distributions/bands/geography in value_json.
OUTCOME_METRICS = (
    "salary_median",  # value_numeric (currency in value_json.currency if not USD)
    "salary_band",  # value_json: {p25,p50,p75,currency}
    "starting_salary_band",  # value_json: {p25,p50,p75,currency}
    "employment_rate",  # value_numeric 0–1
    "underemployment_rate",  # value_numeric 0–1
    "hire_rate",  # value_numeric 0–1
    "internship_to_offer_rate",  # value_numeric 0–1
    "payback_period_months",  # value_numeric months (or value_json band)
    "employer_concentration",  # value_numeric (HHI or top-N share)
    "placement_geography",  # value_json: [{region, share}]
)
OUTCOME_METRIC_CHECK = "metric IN (" + ",".join(f"'{m}'" for m in OUTCOME_METRICS) + ")"

# ── Admissions-history (§3) ─────────────────────────────────────────────────
SELECTIVITY_BANDS = ("most_selective", "highly_selective", "selective", "less_selective", "open")
SELECTIVITY_BAND_CHECK = (
    "selectivity_band IS NULL OR selectivity_band IN ("
    + ",".join(f"'{b}'" for b in SELECTIVITY_BANDS)
    + ")"
)

# Academic-only allowlist for ``class_profile`` (§3 / spec 46 §6). The loop is
# closed deliberately: ``67`` trains on these keys, so NO protected attribute
# (race, gender, name-origin) and NO proxy (ZIP, intl/first-gen share) may enter.
# A CI guard (tests/test_outcomes_class_profile_guard) fails if a row carries a
# key outside this set.
ALLOWED_CLASS_PROFILE_KEYS: frozenset[str] = frozenset(
    {
        "gpa_p25",
        "gpa_p50",
        "gpa_p75",
        "gpa_mean",
        "gpa_scale",  # e.g. 4.0 — the scale the gpa_* values are on
        "test_p25",
        "test_p50",
        "test_p75",
        "test_mean",
        "gre_p50",
        "gmat_p50",
        "sat_p50",
        "act_p50",
        "toefl_p50",
        "ielts_p50",
        "avg_years_experience",
        "years_experience_p50",
        "cohort_size",
    }
)


def disallowed_class_profile_keys(class_profile: dict | None) -> set[str]:
    """Return any ``class_profile`` keys outside the academic allowlist (§3).

    The bias-avoidance guard: admissions history is a ``67`` training feature, so
    a non-academic key (a protected attribute or a demographic proxy) must never
    be stored here. Returns the offending keys; empty set == clean.
    """
    if not class_profile:
        return set()
    return {k for k in class_profile if k not in ALLOWED_CLASS_PROFILE_KEYS}


# ── Mixins for the typed-fact shape ─────────────────────────────────────────
class _OutcomeFactMixin(ProvenanceMixin):
    """The (metric, window, value) shape shared by program/school outcomes."""

    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    value_numeric: Mapped[float | None] = mapped_column(Numeric(14, 4))
    value_json: Mapped[dict | None] = mapped_column(JSONB)
    # Required time window — "a salary with no window is unshippable" (§2).
    reference_period: Mapped[str] = mapped_column(String(32), nullable=False)
    cohort_n: Mapped[int | None] = mapped_column(Integer)


class _AdmissionsHistoryMixin(ProvenanceMixin):
    """Aggregate admit stats per cycle (§3). academic-only ``class_profile``."""

    cycle_year: Mapped[int] = mapped_column(Integer, nullable=False)
    applicants: Mapped[int | None] = mapped_column(Integer)
    admits: Mapped[int | None] = mapped_column(Integer)
    enrolled: Mapped[int | None] = mapped_column(Integer)
    admit_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    yield_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    class_profile: Mapped[dict | None] = mapped_column(JSONB)
    selectivity_band: Mapped[str | None] = mapped_column(String(20))


# ── Program-grain ───────────────────────────────────────────────────────────
class ProgramOutcome(UUIDPrimaryKeyMixin, TimestampMixin, _OutcomeFactMixin, Base):
    __tablename__ = "program_outcomes"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "program_id", "metric", "reference_period", "source", name="uq_program_outcomes_key"
        ),
        CheckConstraint(OUTCOME_METRIC_CHECK, name="ck_program_outcomes_metric"),
        CheckConstraint(OUTCOME_SOURCE_CHECK, name="ck_program_outcomes_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_program_outcomes_status"),
        Index("ix_program_outcomes_program", "program_id"),
        Index("ix_program_outcomes_program_metric", "program_id", "metric"),
    )


class ProgramTopEmployer(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """Top hiring employers by count and recency (§2) — a list, not a scalar."""

    __tablename__ = "program_top_employers"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    employer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    hire_count: Mapped[int | None] = mapped_column(Integer)
    most_recent_hire_year: Mapped[int | None] = mapped_column(Integer)
    reference_period: Mapped[str | None] = mapped_column(String(32))

    __table_args__ = (
        UniqueConstraint(
            "program_id", "employer_name", "source", name="uq_program_top_employers_key"
        ),
        CheckConstraint(OUTCOME_SOURCE_CHECK, name="ck_program_top_employers_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_program_top_employers_status"),
        Index("ix_program_top_employers_program", "program_id"),
    )


class ProgramAdmissionsHistory(UUIDPrimaryKeyMixin, TimestampMixin, _AdmissionsHistoryMixin, Base):
    __tablename__ = "program_admissions_history"

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "program_id", "cycle_year", "source", name="uq_program_admissions_history_key"
        ),
        CheckConstraint(OUTCOME_SOURCE_CHECK, name="ck_program_admissions_history_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_program_admissions_history_status"),
        CheckConstraint(SELECTIVITY_BAND_CHECK, name="ck_program_admissions_history_selectivity"),
        Index("ix_program_admissions_history_program", "program_id"),
        Index("ix_program_admissions_history_program_year", "program_id", "cycle_year"),
    )


# ── School-grain (§4 — kept a distinct fact from program-grain) ─────────────
class SchoolOutcome(UUIDPrimaryKeyMixin, TimestampMixin, _OutcomeFactMixin, Base):
    __tablename__ = "school_outcomes"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "metric", "reference_period", "source", name="uq_school_outcomes_key"
        ),
        CheckConstraint(OUTCOME_METRIC_CHECK, name="ck_school_outcomes_metric"),
        CheckConstraint(OUTCOME_SOURCE_CHECK, name="ck_school_outcomes_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_school_outcomes_status"),
        Index("ix_school_outcomes_school", "school_id"),
        Index("ix_school_outcomes_school_metric", "school_id", "metric"),
    )


class SchoolAdmissionsHistory(UUIDPrimaryKeyMixin, TimestampMixin, _AdmissionsHistoryMixin, Base):
    __tablename__ = "school_admissions_history"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id", "cycle_year", "source", name="uq_school_admissions_history_key"
        ),
        CheckConstraint(OUTCOME_SOURCE_CHECK, name="ck_school_admissions_history_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_school_admissions_history_status"),
        CheckConstraint(SELECTIVITY_BAND_CHECK, name="ck_school_admissions_history_selectivity"),
        Index("ix_school_admissions_history_school", "school_id"),
        Index("ix_school_admissions_history_school_year", "school_id", "cycle_year"),
    )


# ── Review theme-summarisation (§5 — synth over existing review tables) ──────
REVIEW_THEME_TARGET_TYPES = ("program", "school")
REVIEW_THEME_AUDIENCES = ("student", "employer")


class ReviewThemeSummary(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§5 — "what students/employers consistently say" + common tradeoffs,
    synthesised over the existing review tables. ``target_id`` is a soft,
    polymorphic ref (program or school). One read per card: ``dimension_rollup``
    snapshots the existing ``func.avg()`` dims so the card is one row."""

    __tablename__ = "review_theme_summaries"

    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    audience: Mapped[str] = mapped_column(String(16), nullable=False)
    # [{label, sentiment, supporting_review_ids, n}] — "what they consistently say".
    themes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tradeoffs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    dimension_rollup: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    n_reviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    model_version: Mapped[str | None] = mapped_column(String(80))
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint(
            "target_type", "target_id", "audience", name="uq_review_theme_summaries_key"
        ),
        CheckConstraint(
            "target_type IN ('program','school')", name="ck_review_theme_summaries_target_type"
        ),
        CheckConstraint(
            "audience IN ('student','employer')", name="ck_review_theme_summaries_audience"
        ),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_review_theme_summaries_status"),
        Index("ix_review_theme_summaries_target", "target_type", "target_id"),
    )
