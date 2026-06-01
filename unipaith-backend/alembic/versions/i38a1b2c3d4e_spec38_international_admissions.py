"""Spec 38 — International Admissions (institution processing).

Adds the institution-side processing surface beside an application:

- ``international_processing`` — one row per application (credential evaluation,
  English-proficiency verification, country-requirement checklist, I-20/DS-2019
  immigration document, visa-interview tracking).
- ``country_requirement_packs`` — per-institution requirement-pack overrides
  (platform defaults ship in code; this table holds institution edits).
- ``programs.english_policy`` JSONB — accepted English tests + minimum scores +
  waiver rules (§2.2).
- widens ``ck_ai_turns_agent`` for the two new agents (``credential_normalizer``
  + ``country_requirement_advisor``, §5).

Every change is additive and guarded (table-presence / column-presence checks)
so it is a safe no-op against a dev/test DB built from the models via
``create_all``.

Revision ID: i38a1b2c3d4e
Revises: s3637merge1c2d
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "i38a1b2c3d4e"  # pragma: allowlist secret
down_revision = "s3637merge1c2d"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Post-Spec-38 agent vocabulary (chains off the Spec 35+36+37 merge head, whose
# tail vocabulary ends at the two Spec-35 yield agents).
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
    "'credential_normalizer','country_requirement_advisor')"
)
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    # 1) international_processing — one row per application (§4).
    if not _has_table("international_processing"):
        op.create_table(
            "international_processing",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
            # §2.1 credential evaluation
            sa.Column("credential_provider", sa.String(20), nullable=True),
            sa.Column("credential_status", sa.String(20), server_default="none", nullable=False),
            sa.Column("credential_report_ref", sa.String(1000), nullable=True),
            sa.Column("credential_normalized_gpa", sa.Numeric(4, 2), nullable=True),
            sa.Column("credential_source_scale", sa.String(60), nullable=True),
            sa.Column("credential_notes", sa.Text(), nullable=True),
            # §2.2 english proficiency
            sa.Column("english_test", sa.String(10), nullable=True),
            sa.Column("english_score", sa.Numeric(6, 2), nullable=True),
            sa.Column("english_meets_minimum", sa.Boolean(), nullable=True),
            sa.Column(
                "english_waiver_eligible", sa.Boolean(), server_default="false", nullable=False
            ),
            sa.Column("english_waiver_basis", sa.String(255), nullable=True),
            # §2.3 country requirements
            sa.Column("country_requirements", postgresql.JSONB(), nullable=True),
            # §2.4 immigration document
            sa.Column("immigration_doc_type", sa.String(10), nullable=True),
            sa.Column(
                "immigration_doc_status",
                sa.String(20),
                server_default="not_started",
                nullable=False,
            ),
            sa.Column("sevis_id", sa.String(40), nullable=True),
            sa.Column("immigration_issued_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sevis_export", postgresql.JSONB(), nullable=True),
            # §2.5 visa interview
            sa.Column("visa_appointment_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("visa_consulate", sa.String(120), nullable=True),
            sa.Column("visa_outcome", sa.String(10), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("application_id", name="uq_intl_processing_application"),
            sa.CheckConstraint(
                "credential_provider IS NULL OR credential_provider IN "
                "('WES','ECE','SpanTran','other')",
                name="ck_intl_credential_provider",
            ),
            sa.CheckConstraint(
                "credential_status IN ('none','requested','in_progress','received','verified')",
                name="ck_intl_credential_status",
            ),
            sa.CheckConstraint(
                "english_test IS NULL OR english_test IN ('TOEFL','IELTS','DET','PTE')",
                name="ck_intl_english_test",
            ),
            sa.CheckConstraint(
                "immigration_doc_type IS NULL OR immigration_doc_type IN ('I-20','DS-2019')",
                name="ck_intl_immigration_doc_type",
            ),
            sa.CheckConstraint(
                "immigration_doc_status IN ('not_started','drafted','issued','sent','received')",
                name="ck_intl_immigration_doc_status",
            ),
            sa.CheckConstraint(
                "visa_outcome IS NULL OR visa_outcome IN ('pending','approved','denied')",
                name="ck_intl_visa_outcome",
            ),
        )
        op.create_index(
            "ix_international_processing_application_id",
            "international_processing",
            ["application_id"],
        )
        op.create_index(
            "ix_intl_processing_institution",
            "international_processing",
            ["institution_id"],
        )

    # 2) country_requirement_packs — institution overrides (defaults ship in code).
    if not _has_table("country_requirement_packs"):
        op.create_table(
            "country_requirement_packs",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("country_code", sa.String(2), nullable=False),
            sa.Column("country_name", sa.String(120), nullable=False),
            sa.Column("requirements", postgresql.JSONB(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
            sa.UniqueConstraint(
                "institution_id", "country_code", name="uq_country_pack_inst_country"
            ),
        )
        op.create_index(
            "ix_country_requirement_packs_institution_id",
            "country_requirement_packs",
            ["institution_id"],
        )
        op.create_index(
            "ix_country_pack_country",
            "country_requirement_packs",
            ["country_code"],
        )
        # Postgres treats NULLs as distinct, so the plain unique constraint above
        # cannot dedupe platform defaults (institution_id IS NULL). A partial
        # unique index enforces one platform-default row per country.
        op.create_index(
            "uq_country_pack_platform_default",
            "country_requirement_packs",
            ["country_code"],
            unique=True,
            postgresql_where=sa.text("institution_id IS NULL"),
        )

    # 3) programs.english_policy — §2.2 English-proficiency policy.
    if _has_table("programs") and "english_policy" not in _columns("programs"):
        op.add_column("programs", sa.Column("english_policy", postgresql.JSONB(), nullable=True))

    # 4) ai_turns — widen the agent CHECK for the two new Spec-38 agents (§5).
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

    if _has_table("programs") and "english_policy" in _columns("programs"):
        op.drop_column("programs", "english_policy")

    if _has_table("country_requirement_packs"):
        op.drop_table("country_requirement_packs")

    if _has_table("international_processing"):
        op.drop_table("international_processing")
