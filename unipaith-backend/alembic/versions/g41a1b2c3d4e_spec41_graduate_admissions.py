"""Spec 41 — Graduate & PhD Admissions.

Adds the graduate-specific admissions layer on top of the shared pipeline:
``departments`` + ``programs.department_id`` (the reviewing department), the
faculty roster (``faculty_profiles``) + advisor matching (``advisor_matches``),
the applicant's grad intent (``graduate_intents``), the funding-package builder
(``funding_pools`` + ``funding_packages`` + ``funding_package_components``), and
the two-stage department review (``department_reviews``). Adds the ``faculty``
value to the ``user_role`` enum (§8) and widens ``ck_ai_turns_agent`` for the
three graduate agents (``advisor_matcher`` + ``sop_interest_extractor`` +
``funding_scenario_helper``, §5).

Every table create is guarded (``_has_table``) so the migration is a safe no-op
against a dev/test DB built from the models via ``create_all`` (conftest path).

Revision ID: g41a1b2c3d4e
Revises: b12c0de5f7a9
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "g41a1b2c3d4e"  # pragma: allowlist secret
# Rebased onto the current single head after the Spec-39-polish / billing branch
# (b12c0de5f7a9) merged ahead of this one. It also chained off r40a1b2c3d4e, so
# re-pointing here keeps the graph single-headed (test_alembic_has_single_head).
# b12c added no agents, so the post-Spec-40 agent vocabulary below is unchanged.
down_revision = "b12c0de5f7a9"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Post-Spec-41 agent vocabulary (adds the three graduate agents to the post-
# Spec-40 set).
_AGENT_CHECK_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield',"
    "'credential_normalizer','country_requirement_advisor',"
    "'prospect_prioritizer','territory_optimizer',"
    "'advisor_matcher','sop_interest_extractor','funding_scenario_helper')"
)
# Prior state (the down_revision's vocabulary — Spec 40 added the two CRM agents).
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield',"
    "'credential_normalizer','country_requirement_advisor',"
    "'prospect_prioritizer','territory_optimizer')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return any(c["name"] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def _ts_cols() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    # 0) user_role enum — add the `faculty` value (§8). Autocommit block so the
    #    ADD VALUE is safe across PG configs; IF NOT EXISTS keeps it idempotent
    #    (create_all builds the enum with `faculty` already in the test path).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'faculty'")

    # 1) departments (FK target for faculty / pools / programs).
    if not _has_table("departments"):
        op.create_table(
            "departments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("code", sa.String(40), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.UniqueConstraint("institution_id", "name", name="uq_departments_inst_name"),
            *_ts_cols(),
        )
        op.create_index("ix_departments_inst", "departments", ["institution_id"])

    # 1b) programs.department_id (link program → reviewing department).
    if not _has_column("programs", "department_id"):
        op.add_column(
            "programs",
            sa.Column(
                "department_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("departments.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    # 2) faculty_profiles.
    if not _has_table("faculty_profiles"):
        op.create_table(
            "faculty_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "department_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("departments.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("email", sa.String(255), nullable=True),
            sa.Column("title", sa.String(255), nullable=True),
            sa.Column("research_areas", postgresql.JSONB(), nullable=True),
            sa.Column("accepting_students", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("openings", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("funding_available", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("homepage_url", sa.String(1000), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_faculty_profiles_inst", "faculty_profiles", ["institution_id"])
        op.create_index("ix_faculty_profiles_dept", "faculty_profiles", ["department_id"])
        op.create_index("ix_faculty_profiles_user", "faculty_profiles", ["user_id"])

    # 3) graduate_intents (1:1 with application).
    if not _has_table("graduate_intents"):
        op.create_table(
            "graduate_intents",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "application_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("applications.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("research_interests", postgresql.JSONB(), nullable=True),
            sa.Column("target_advisor_ids", postgresql.JSONB(), nullable=True),
            sa.Column("target_advisor_names", postgresql.JSONB(), nullable=True),
            sa.Column("statement_of_purpose", sa.Text(), nullable=True),
            sa.Column("funding_required", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("extracted_interests", postgresql.JSONB(), nullable=True),
            sa.Column("alignment_summary", sa.Text(), nullable=True),
            sa.UniqueConstraint("application_id", name="uq_graduate_intents_app"),
            *_ts_cols(),
        )

    # 4) advisor_matches.
    if not _has_table("advisor_matches"):
        op.create_table(
            "advisor_matches",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "application_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("applications.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "faculty_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("faculty_profiles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("alignment_score", sa.Numeric(5, 2), nullable=True),
            sa.Column(
                "applicant_named_advisor", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column(
                "advisor_flagged_interest", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column("mutual", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("rationale", sa.Text(), nullable=True),
            sa.UniqueConstraint(
                "application_id", "faculty_id", name="uq_advisor_match_app_faculty"
            ),
            *_ts_cols(),
        )
        op.create_index("ix_advisor_matches_app", "advisor_matches", ["application_id"])
        op.create_index("ix_advisor_matches_faculty", "advisor_matches", ["faculty_id"])

    # 5) funding_pools.
    if not _has_table("funding_pools"):
        op.create_table(
            "funding_pools",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "department_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("departments.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("kind", sa.String(20), nullable=False, server_default="department"),
            sa.Column("total_budget", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.CheckConstraint(
                "kind IN ('department','grant','fellowship','other')",
                name="ck_funding_pools_kind",
            ),
            *_ts_cols(),
        )
        op.create_index("ix_funding_pools_inst", "funding_pools", ["institution_id"])
        op.create_index("ix_funding_pools_dept", "funding_pools", ["department_id"])

    # 6) funding_packages (1:1 with application).
    if not _has_table("funding_packages"):
        op.create_table(
            "funding_packages",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "application_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("applications.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "department_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("departments.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("total_value", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
            sa.Column("multi_year", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "proposed_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("application_id", name="uq_funding_packages_app"),
            sa.CheckConstraint(
                "status IN ('draft','proposed','finalized','rescinded')",
                name="ck_funding_packages_status",
            ),
            *_ts_cols(),
        )
        op.create_index("ix_funding_packages_dept", "funding_packages", ["department_id"])

    # 7) funding_package_components.
    if not _has_table("funding_package_components"):
        op.create_table(
            "funding_package_components",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "package_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("funding_packages.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("kind", sa.String(20), nullable=False),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
            sa.Column(
                "source_pool_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("funding_pools.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("years", postgresql.JSONB(), nullable=True),
            sa.Column("label", sa.String(255), nullable=True),
            sa.CheckConstraint(
                "kind IN ('TA','RA','fellowship','tuition_waiver','stipend')",
                name="ck_funding_components_kind",
            ),
            *_ts_cols(),
        )
        op.create_index(
            "ix_funding_components_package", "funding_package_components", ["package_id"]
        )
        op.create_index(
            "ix_funding_components_pool", "funding_package_components", ["source_pool_id"]
        )

    # 8) department_reviews (1:1 with application — two-stage release record).
    if not _has_table("department_reviews"):
        op.create_table(
            "department_reviews",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "application_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("applications.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "department_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("departments.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("recommended_decision", sa.String(30), nullable=True),
            sa.Column(
                "recommended_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("recommended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("committee_notes", sa.Text(), nullable=True),
            sa.Column(
                "funding_package_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("funding_packages.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("central_status", sa.String(20), nullable=True),
            sa.Column(
                "central_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("central_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("central_decision", sa.String(30), nullable=True),
            sa.UniqueConstraint("application_id", name="uq_department_reviews_app"),
            sa.CheckConstraint(
                "central_status IS NULL OR central_status IN ('pending','confirmed','overridden')",
                name="ck_department_reviews_central_status",
            ),
            *_ts_cols(),
        )
        op.create_index("ix_department_reviews_dept", "department_reviews", ["department_id"])

    # 9) ai_turns — widen the agent CHECK for the three graduate agents (§5).
    if _has_table("ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        op.execute(
            f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_AGENT_CHECK_NEW})"
        )


def downgrade() -> None:
    if _has_table("ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        op.execute(
            f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_AGENT_CHECK_OLD})"
        )

    for tbl in (
        "department_reviews",
        "funding_package_components",
        "funding_packages",
        "advisor_matches",
        "graduate_intents",
        "faculty_profiles",
        "funding_pools",
    ):
        if _has_table(tbl):
            op.drop_table(tbl)

    if _has_column("programs", "department_id"):
        op.drop_column("programs", "department_id")

    if _has_table("departments"):
        op.drop_table("departments")
    # Note: the `faculty` enum value is intentionally NOT removed on downgrade —
    # Postgres cannot drop an enum value, and leaving it is harmless.
