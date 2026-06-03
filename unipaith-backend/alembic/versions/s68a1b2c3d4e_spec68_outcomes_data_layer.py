"""Spec 68 — Outcomes & Admissions-History Data Layer (typed, not JSONB).

Adds the typed projection that replaces the untyped ``Program.outcomes_data`` /
``cost_data`` blobs and the fabricated ``HistoricalOutcome`` rows:

- ``program_outcomes`` / ``school_outcomes`` — (metric, window, value) facts,
  closed metric enum, scalar or JSON payload, required reference window (§2).
- ``program_top_employers`` — top hiring employers by count/recency (§2).
- ``program_admissions_history`` / ``school_admissions_history`` — aggregate
  admit stats per cycle; academic-only ``class_profile`` (§3 / spec 46 §6).
- ``review_theme_summaries`` — synthesised "what they consistently say" + common
  tradeoffs over the existing review tables (§5).

Every fact carries the provenance envelope (``ProvenanceMixin``). Outcomes use an
outcomes-specific source vocabulary (``crawled`` < ``licensed`` < ``reported``,
§7) — distinct from the crawler's ``KNOWLEDGE_SOURCES`` because licensed
government data (IPEDS / Scorecard) is high-trust for outcomes.

Every create is guarded (``_has_table``) so the migration is a safe no-op against
a dev/test DB built from the models via ``create_all`` (the conftest path), and
runs incrementally in production from the prior head.

Revision ID: s68a1b2c3d4e
Revises: s60a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s68a1b2c3d4e"  # pragma: allowlist secret
# Re-pointed onto e62a1b2c3d4e (Spec 62 eval-harness head; chain s60→s63→e62) when
# Spec 62/63 merged to main concurrently — s68's tables are independent of theirs,
# so this is pure linearization to keep the graph single-headed
# (test_alembic_has_single_head).
down_revision = "e62a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_OUTCOME_SOURCE_CHECK = "source IN ('crawled','licensed','reported')"
_STATUS_CHECK = "status IN ('provisional','live','review','superseded','archived')"
_METRIC_CHECK = (
    "metric IN ('salary_median','salary_band','starting_salary_band','employment_rate',"
    "'underemployment_rate','hire_rate','internship_to_offer_rate','payback_period_months',"
    "'employer_concentration','placement_geography')"
)
_SELECTIVITY_CHECK = (
    "selectivity_band IS NULL OR selectivity_band IN "
    "('most_selective','highly_selective','selective','less_selective','open')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _id() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _provenance() -> list[sa.Column]:
    """The §4 provenance envelope (matches ``crawler.ProvenanceMixin``)."""
    return [
        sa.Column("source", sa.String(24), nullable=False, server_default="crawled"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_domain", sa.String(255), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="provisional"),
    ]


def _outcome_fact_cols() -> list[sa.Column]:
    return [
        sa.Column("metric", sa.String(40), nullable=False),
        sa.Column("value_numeric", sa.Numeric(14, 4), nullable=True),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reference_period", sa.String(32), nullable=False),
        sa.Column("cohort_n", sa.Integer(), nullable=True),
    ]


def _admissions_cols() -> list[sa.Column]:
    return [
        sa.Column("cycle_year", sa.Integer(), nullable=False),
        sa.Column("applicants", sa.Integer(), nullable=True),
        sa.Column("admits", sa.Integer(), nullable=True),
        sa.Column("enrolled", sa.Integer(), nullable=True),
        sa.Column("admit_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("yield_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("class_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("selectivity_band", sa.String(20), nullable=True),
    ]


def _create_program_outcomes() -> None:
    if _has_table("program_outcomes"):
        return
    op.create_table(
        "program_outcomes",
        _id(),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_outcome_fact_cols(),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "program_id", "metric", "reference_period", "source", name="uq_program_outcomes_key"
        ),
        sa.CheckConstraint(_METRIC_CHECK, name="ck_program_outcomes_metric"),
        sa.CheckConstraint(_OUTCOME_SOURCE_CHECK, name="ck_program_outcomes_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_program_outcomes_status"),
    )
    op.create_index("ix_program_outcomes_program", "program_outcomes", ["program_id"])
    op.create_index(
        "ix_program_outcomes_program_metric", "program_outcomes", ["program_id", "metric"]
    )


def _create_program_top_employers() -> None:
    if _has_table("program_top_employers"):
        return
    op.create_table(
        "program_top_employers",
        _id(),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("employer_name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("hire_count", sa.Integer(), nullable=True),
        sa.Column("most_recent_hire_year", sa.Integer(), nullable=True),
        sa.Column("reference_period", sa.String(32), nullable=True),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "program_id", "employer_name", "source", name="uq_program_top_employers_key"
        ),
        sa.CheckConstraint(_OUTCOME_SOURCE_CHECK, name="ck_program_top_employers_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_program_top_employers_status"),
    )
    op.create_index("ix_program_top_employers_program", "program_top_employers", ["program_id"])


def _create_program_admissions_history() -> None:
    if _has_table("program_admissions_history"):
        return
    op.create_table(
        "program_admissions_history",
        _id(),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_admissions_cols(),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "program_id", "cycle_year", "source", name="uq_program_admissions_history_key"
        ),
        sa.CheckConstraint(_OUTCOME_SOURCE_CHECK, name="ck_program_admissions_history_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_program_admissions_history_status"),
        sa.CheckConstraint(_SELECTIVITY_CHECK, name="ck_program_admissions_history_selectivity"),
    )
    op.create_index(
        "ix_program_admissions_history_program", "program_admissions_history", ["program_id"]
    )
    op.create_index(
        "ix_program_admissions_history_program_year",
        "program_admissions_history",
        ["program_id", "cycle_year"],
    )


def _create_school_outcomes() -> None:
    if _has_table("school_outcomes"):
        return
    op.create_table(
        "school_outcomes",
        _id(),
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_outcome_fact_cols(),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "school_id", "metric", "reference_period", "source", name="uq_school_outcomes_key"
        ),
        sa.CheckConstraint(_METRIC_CHECK, name="ck_school_outcomes_metric"),
        sa.CheckConstraint(_OUTCOME_SOURCE_CHECK, name="ck_school_outcomes_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_school_outcomes_status"),
    )
    op.create_index("ix_school_outcomes_school", "school_outcomes", ["school_id"])
    op.create_index("ix_school_outcomes_school_metric", "school_outcomes", ["school_id", "metric"])


def _create_school_admissions_history() -> None:
    if _has_table("school_admissions_history"):
        return
    op.create_table(
        "school_admissions_history",
        _id(),
        sa.Column(
            "school_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_admissions_cols(),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "school_id", "cycle_year", "source", name="uq_school_admissions_history_key"
        ),
        sa.CheckConstraint(_OUTCOME_SOURCE_CHECK, name="ck_school_admissions_history_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_school_admissions_history_status"),
        sa.CheckConstraint(_SELECTIVITY_CHECK, name="ck_school_admissions_history_selectivity"),
    )
    op.create_index(
        "ix_school_admissions_history_school", "school_admissions_history", ["school_id"]
    )
    op.create_index(
        "ix_school_admissions_history_school_year",
        "school_admissions_history",
        ["school_id", "cycle_year"],
    )


def _create_review_theme_summaries() -> None:
    if _has_table("review_theme_summaries"):
        return
    op.create_table(
        "review_theme_summaries",
        _id(),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audience", sa.String(16), nullable=False),
        sa.Column(
            "themes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "tradeoffs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "dimension_rollup",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("n_reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model_version", sa.String(80), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "target_type", "target_id", "audience", name="uq_review_theme_summaries_key"
        ),
        sa.CheckConstraint(
            "target_type IN ('program','school')", name="ck_review_theme_summaries_target_type"
        ),
        sa.CheckConstraint(
            "audience IN ('student','employer')", name="ck_review_theme_summaries_audience"
        ),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_review_theme_summaries_status"),
    )
    op.create_index(
        "ix_review_theme_summaries_target",
        "review_theme_summaries",
        ["target_type", "target_id"],
    )


def upgrade() -> None:
    _create_program_outcomes()
    _create_program_top_employers()
    _create_program_admissions_history()
    _create_school_outcomes()
    _create_school_admissions_history()
    _create_review_theme_summaries()


def downgrade() -> None:
    for tbl in (
        "review_theme_summaries",
        "school_admissions_history",
        "school_outcomes",
        "program_admissions_history",
        "program_top_employers",
        "program_outcomes",
    ):
        if _has_table(tbl):
            op.drop_table(tbl)
