"""Spec 40 — Recruitment CRM (Pre-Applicant).

Adds the institution top-of-funnel: ``prospects`` (pre-applicant records with a
forward link to ``applications``), ``recruitment_trips`` + ``trip_visits``
(travel calendar), ``recruitment_fairs`` (HS / college-fair directory), and
``territories`` (territory management). Widens ``ck_ai_turns_agent`` for the two
new recruitment agents (``prospect_prioritizer`` + ``territory_optimizer``, §5).

Every table create is guarded (``_has_table``) so the migration is a safe no-op
against a dev/test DB built from the models via ``create_all`` (conftest path).

Revision ID: r40a1b2c3d4e
Revises: s3637merge1c2d
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "r40a1b2c3d4e"  # pragma: allowlist secret
# Rebased onto the Spec 38 head (i38a1b2c3d4e) after it merged ahead of this
# branch — both originally chained off s3637merge1c2d, which would have left two
# heads. Re-pointing keeps the graph single-headed (test_alembic_has_single_head).
down_revision = "i38a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Post-Spec-40 agent vocabulary (adds the two recruitment agents to the post-
# Spec-38 set; Spec 36/37 added no agents, Spec 38 added the two intl agents).
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
    "'prospect_prioritizer','territory_optimizer')"
)
# Prior state (the down_revision's vocabulary — Spec 38 added the two intl agents).
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
    "'credential_normalizer','country_requirement_advisor')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


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
    # 1) territories (referenced by prospects.territory_id) — create first.
    if not _has_table("territories"):
        op.create_table(
            "territories",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("geo", postgresql.JSONB(), nullable=True),
            sa.Column(
                "owner_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("owner_name", sa.String(255), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            *_ts_cols(),
        )
        op.create_index("ix_territories_inst", "territories", ["institution_id"])

    # 2) recruitment_fairs (referenced by trip_visits.fair_id).
    if not _has_table("recruitment_fairs"):
        op.create_table(
            "recruitment_fairs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("kind", sa.String(12), nullable=False, server_default="fair"),
            sa.Column("city", sa.String(120), nullable=True),
            sa.Column("region", sa.String(120), nullable=True),
            sa.Column("country", sa.String(100), nullable=True),
            sa.Column("contact_name", sa.String(255), nullable=True),
            sa.Column("contact_email", sa.String(255), nullable=True),
            sa.Column("prior_year_yield", sa.Integer(), nullable=True),
            sa.Column("event_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(14), nullable=False, server_default="prospective"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.CheckConstraint("kind IN ('fair','high_school')", name="ck_recruitment_fairs_kind"),
            sa.CheckConstraint(
                "status IN ('prospective','registered','confirmed','attended','skipped')",
                name="ck_recruitment_fairs_status",
            ),
            *_ts_cols(),
        )
        op.create_index("ix_recruitment_fairs_inst", "recruitment_fairs", ["institution_id"])

    # 3) prospects.
    if not _has_table("prospects"):
        op.create_table(
            "prospects",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("email", sa.String(255), nullable=True),
            sa.Column("phone", sa.String(50), nullable=True),
            sa.Column("city", sa.String(120), nullable=True),
            sa.Column("region", sa.String(120), nullable=True),
            sa.Column("country", sa.String(100), nullable=True),
            sa.Column("interests", postgresql.JSONB(), nullable=True),
            sa.Column("source", sa.String(20), nullable=False, server_default="web"),
            sa.Column("source_detail", sa.String(255), nullable=True),
            sa.Column("stage", sa.String(20), nullable=False, server_default="prospect"),
            sa.Column(
                "territory_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("territories.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "owner_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("owner_name", sa.String(255), nullable=True),
            sa.Column(
                "converted_application_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("applications.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("consent_outreach", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("apply_likelihood", sa.Float(), nullable=True),
            sa.Column("priority_reason", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.CheckConstraint(
                "source IN ('fair','list','inquiry','referral','web','visit')",
                name="ck_prospects_source",
            ),
            sa.CheckConstraint(
                "stage IN ('suspect','prospect','engaged','inquiry','applicant')",
                name="ck_prospects_stage",
            ),
            *_ts_cols(),
        )
        op.create_index("ix_prospects_institution_id", "prospects", ["institution_id"])
        op.create_index("ix_prospects_inst_stage", "prospects", ["institution_id", "stage"])
        op.create_index("ix_prospects_inst_source", "prospects", ["institution_id", "source"])
        op.create_index(
            "ix_prospects_inst_territory", "prospects", ["institution_id", "territory_id"]
        )
        op.create_index("ix_prospects_inst_owner", "prospects", ["institution_id", "owner_user_id"])
        op.create_index("ix_prospects_inst_email", "prospects", ["institution_id", "email"])

    # 4) recruitment_trips.
    if not _has_table("recruitment_trips"):
        op.create_table(
            "recruitment_trips",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("region", sa.String(120), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column(
                "recruiter_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("recruiter_name", sa.String(255), nullable=True),
            sa.Column("budget", sa.Numeric(12, 2), nullable=True),
            sa.Column("spend", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.CheckConstraint(
                "status IN ('planned','active','done','cancelled')",
                name="ck_recruitment_trips_status",
            ),
            *_ts_cols(),
        )
        op.create_index(
            "ix_recruitment_trips_institution_id", "recruitment_trips", ["institution_id"]
        )
        op.create_index(
            "ix_recruitment_trips_inst_start", "recruitment_trips", ["institution_id", "start_date"]
        )
        op.create_index(
            "ix_recruitment_trips_recruiter",
            "recruitment_trips",
            ["institution_id", "recruiter_user_id"],
        )

    # 5) trip_visits.
    if not _has_table("trip_visits"):
        op.create_table(
            "trip_visits",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "trip_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("recruitment_trips.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("kind", sa.String(10), nullable=False, server_default="school"),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column(
                "fair_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("recruitment_fairs.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("visit_date", sa.Date(), nullable=True),
            sa.Column("prospects_met", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(12), nullable=False, server_default="planned"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.CheckConstraint("kind IN ('school','fair')", name="ck_trip_visits_kind"),
            sa.CheckConstraint(
                "status IN ('planned','confirmed','done')", name="ck_trip_visits_status"
            ),
            *_ts_cols(),
        )
        op.create_index("ix_trip_visits_trip", "trip_visits", ["trip_id"])

    # 6) ai_turns — widen the agent CHECK for the two recruitment agents (§5).
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
        "trip_visits",
        "recruitment_trips",
        "prospects",
        "recruitment_fairs",
        "territories",
    ):
        if _has_table(tbl):
            op.drop_table(tbl)
