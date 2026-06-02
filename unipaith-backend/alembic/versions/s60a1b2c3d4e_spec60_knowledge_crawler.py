"""Spec 60 — Data Crawler & Knowledge-Base Engine.

Wires the dormant ``knowledge.py`` skeleton into a governed enrichment engine:

- ``crawl_sources`` — the allowlisted source registry + policy (§2 / §11).
- ``knowledge_entities`` — the canonical entity node the skeleton referenced but
  never migrated (§16).
- ``entity_enrichments`` — the provenance / audit write-path (§7).
- ``change_events`` — the proactive change feed (§3B / §15); distinct from spec
  44's ``signal_change_events``.
- ``scholarships`` (§5.1) + the reference projection ``ref_*`` /
  ``reference_entities`` (§5.2), each carrying provenance.

Every create is guarded (``_has_table``) so the migration is a safe no-op against
a dev/test DB built from the models via ``create_all`` (the conftest path), and
runs incrementally in production from the prior head.

Revision ID: s60a1b2c3d4e
Revises: s56a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s60a1b2c3d4e"  # pragma: allowlist secret
# s56a1b2c3d4e (Spec 56 saved-searches) is the single head at branch time; chain
# off it to keep the graph single-headed (test_alembic_has_single_head).
down_revision = "s56a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_SOURCE_CHECK = "source IN ('seed','crawled','corroborated','first_party','institution_verified')"
_STATUS_CHECK = "status IN ('provisional','live','review','superseded','archived')"


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


def _jsonb(name: str, default: str) -> sa.Column:
    return sa.Column(
        name,
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text(default),
    )


def _create_crawl_sources() -> None:
    if _has_table("crawl_sources"):
        return
    op.create_table(
        "crawl_sources",
        _id(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("publisher_kind", sa.String(24), nullable=False, server_default="official"),
        sa.Column("trust_tier", sa.Integer(), nullable=False, server_default="2"),
        _jsonb("domain_tags", "'[]'::jsonb"),
        sa.Column("volatility_tier", sa.String(16), nullable=False, server_default="standard"),
        _jsonb("crawl_config", "'{}'::jsonb"),
        sa.Column("cadence_hours", sa.Integer(), nullable=False, server_default="720"),
        sa.Column("allowlisted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("respect_robots", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "requires_attribution", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("license", sa.String(120), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("trust_tier BETWEEN 1 AND 4", name="ck_crawl_sources_trust_tier"),
        sa.CheckConstraint(
            "publisher_kind IN ('official','government','academic','ranking','aggregator')",
            name="ck_crawl_sources_publisher_kind",
        ),
    )
    op.create_index("ix_crawl_sources_enabled", "crawl_sources", ["enabled", "allowlisted"])
    op.create_index("ix_crawl_sources_domain", "crawl_sources", ["domain"])


def _create_knowledge_entities() -> None:
    if _has_table("knowledge_entities"):
        return
    op.create_table(
        "knowledge_entities",
        _id(),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("canonical_name", sa.String(500), nullable=False),
        sa.Column("canonical_key", sa.String(120), nullable=True),
        sa.Column("domain", sa.String(40), nullable=True),
        _jsonb("aliases", "'[]'::jsonb"),
        _jsonb("attributes", "'{}'::jsonb"),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint("entity_type", "canonical_key", name="uq_knowledge_entities_type_key"),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_knowledge_entities_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_knowledge_entities_status"),
    )
    op.create_index("ix_knowledge_entities_type", "knowledge_entities", ["entity_type"])
    op.create_index("ix_knowledge_entities_name", "knowledge_entities", ["canonical_name"])


def _create_entity_enrichments() -> None:
    if _has_table("entity_enrichments"):
        return
    op.create_table(
        "entity_enrichments",
        _id(),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_key", sa.String(120), nullable=True),
        sa.Column("field_path", sa.String(120), nullable=False),
        _jsonb("proposed_value", "'{}'::jsonb"),
        sa.Column("current_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(24), nullable=False, server_default="crawled"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("review_reason", sa.String(120), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending','applied','review','rejected','superseded')",
            name="ck_entity_enrichments_status",
        ),
    )
    op.create_index(
        "ix_entity_enrichments_target", "entity_enrichments", ["target_type", "target_id"]
    )
    op.create_index("ix_entity_enrichments_status", "entity_enrichments", ["status"])
    op.create_index(
        "ix_entity_enrichments_target_field",
        "entity_enrichments",
        ["target_type", "target_key", "field_path"],
    )


def _create_change_events() -> None:
    if _has_table("change_events"):
        return
    op.create_table(
        "change_events",
        _id(),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_name", sa.String(500), nullable=True),
        sa.Column("change_type", sa.String(40), nullable=False),
        sa.Column("field_path", sa.String(120), nullable=True),
        sa.Column("old_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("materiality", sa.String(10), nullable=False, server_default="low"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(12), nullable=False, server_default="pending"),
        sa.Column("routed_at", sa.DateTime(timezone=True), nullable=True),
        _jsonb("routing", "'{}'::jsonb"),
        *_timestamps(),
        sa.CheckConstraint(
            "materiality IN ('high','medium','low')", name="ck_change_events_materiality"
        ),
        sa.CheckConstraint(
            "status IN ('pending','routed','dismissed')", name="ck_change_events_status"
        ),
    )
    op.create_index("ix_change_events_target", "change_events", ["target_type", "target_id"])
    op.create_index(
        "ix_change_events_status_materiality", "change_events", ["status", "materiality"]
    )
    op.create_index("ix_change_events_detected_at", "change_events", ["detected_at"])


def _create_scholarships() -> None:
    if _has_table("scholarships"):
        return
    op.create_table(
        "scholarships",
        _id(),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False, unique=True),
        sa.Column("scholarship_type", sa.String(24), nullable=False, server_default="external"),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sponsor", sa.String(300), nullable=True),
        sa.Column("amount_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("amount_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("is_renewable", sa.Boolean(), nullable=True),
        _jsonb("eligibility", "'{}'::jsonb"),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("application_url", sa.Text(), nullable=True),
        _jsonb("distribution_history", "'{}'::jsonb"),
        *_provenance(),
        *_timestamps(),
        sa.CheckConstraint(
            "scholarship_type IN ('merit','need','external','institutional','departmental')",
            name="ck_scholarships_type",
        ),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_scholarships_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_scholarships_status"),
    )
    op.create_index("ix_scholarships_institution", "scholarships", ["institution_id"])
    op.create_index("ix_scholarships_program", "scholarships", ["program_id"])
    op.create_index("ix_scholarships_type", "scholarships", ["scholarship_type"])


def _create_ref_occupations() -> None:
    if _has_table("ref_occupations"):
        return
    op.create_table(
        "ref_occupations",
        _id(),
        sa.Column("soc_code", sa.String(12), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("median_salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("employment", sa.Integer(), nullable=True),
        sa.Column("projected_growth_pct", sa.Float(), nullable=True),
        sa.Column("outlook", sa.String(40), nullable=True),
        sa.Column("education_typical", sa.String(120), nullable=True),
        _jsonb("related_majors", "'[]'::jsonb"),
        *_provenance(),
        *_timestamps(),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_occupations_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_occupations_status"),
    )
    op.create_index("ix_ref_occupations_title", "ref_occupations", ["title"])


def _create_ref_tests() -> None:
    if _has_table("ref_tests"):
        return
    op.create_table(
        "ref_tests",
        _id(),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(24), nullable=False, server_default="other"),
        _jsonb("sections", "'[]'::jsonb"),
        sa.Column("score_min", sa.Float(), nullable=True),
        sa.Column("score_max", sa.Float(), nullable=True),
        sa.Column("validity_years", sa.Integer(), nullable=True),
        sa.Column("superscore_allowed", sa.Boolean(), nullable=True),
        *_provenance(),
        *_timestamps(),
        sa.CheckConstraint(
            "category IN ('english','graduate','undergraduate','subject','other')",
            name="ck_ref_tests_category",
        ),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_tests_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_tests_status"),
    )


def _create_ref_visas() -> None:
    if _has_table("ref_visas"):
        return
    op.create_table(
        "ref_visas",
        _id(),
        sa.Column("country", sa.String(60), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        _jsonb("requirements", "'{}'::jsonb"),
        _jsonb("work_rights", "'{}'::jsonb"),
        sa.Column("duration", sa.String(120), nullable=True),
        sa.Column("financial_proof_required", sa.Boolean(), nullable=True),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint("country", "code", name="uq_ref_visas_country_code"),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_visas_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_visas_status"),
    )
    op.create_index("ix_ref_visas_country", "ref_visas", ["country"])


def _create_ref_geo_cost() -> None:
    if _has_table("ref_geo_cost"):
        return
    op.create_table(
        "ref_geo_cost",
        _id(),
        sa.Column("locale", sa.String(160), nullable=False),
        sa.Column("country", sa.String(60), nullable=False),
        sa.Column("cost_of_living_index", sa.Float(), nullable=True),
        sa.Column("rent_index", sa.Float(), nullable=True),
        sa.Column("monthly_estimate", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint("country", "locale", name="uq_ref_geo_cost_country_locale"),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_geo_cost_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_geo_cost_status"),
    )


def _create_ref_majors() -> None:
    if _has_table("ref_majors"):
        return
    op.create_table(
        "ref_majors",
        _id(),
        sa.Column("cip_code", sa.String(12), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        _jsonb("typical_curriculum", "'[]'::jsonb"),
        _jsonb("prerequisites", "'[]'::jsonb"),
        _jsonb("related_occupations", "'[]'::jsonb"),
        *_provenance(),
        *_timestamps(),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_majors_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_majors_status"),
    )
    op.create_index("ix_ref_majors_title", "ref_majors", ["title"])


def _create_ref_rankings() -> None:
    if _has_table("ref_rankings"):
        return
    op.create_table(
        "ref_rankings",
        _id(),
        sa.Column("ranker", sa.String(120), nullable=False),
        sa.Column("entity_name", sa.String(300), nullable=False),
        sa.Column("entity_type", sa.String(24), nullable=False, server_default="institution"),
        sa.Column("scope", sa.String(120), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "ranker", "entity_name", "scope", "year", name="uq_ref_rankings_subject_year"
        ),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_rankings_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_rankings_status"),
    )
    op.create_index("ix_ref_rankings_entity", "ref_rankings", ["entity_name"])


def _create_ref_accreditation() -> None:
    if _has_table("ref_accreditation"):
        return
    op.create_table(
        "ref_accreditation",
        _id(),
        sa.Column("body", sa.String(200), nullable=False),
        sa.Column("body_type", sa.String(24), nullable=False, server_default="regional"),
        sa.Column("entity_name", sa.String(300), nullable=False),
        sa.Column("accreditation_status", sa.String(60), nullable=True),
        sa.Column("scope", sa.String(200), nullable=True),
        sa.Column("valid_through", sa.Date(), nullable=True),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint(
            "body", "entity_name", "scope", name="uq_ref_accreditation_body_entity"
        ),
        sa.CheckConstraint(
            "body_type IN ('regional','national','programmatic')",
            name="ck_ref_accreditation_body_type",
        ),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_accreditation_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_accreditation_status"),
    )
    op.create_index("ix_ref_accreditation_entity", "ref_accreditation", ["entity_name"])


def _create_reference_entities() -> None:
    if _has_table("reference_entities"):
        return
    op.create_table(
        "reference_entities",
        _id(),
        sa.Column("ref_type", sa.String(60), nullable=False),
        sa.Column("ref_key", sa.String(160), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        _jsonb("data", "'{}'::jsonb"),
        *_provenance(),
        *_timestamps(),
        sa.UniqueConstraint("ref_type", "ref_key", name="uq_reference_entities_type_key"),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_reference_entities_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_reference_entities_status"),
    )
    op.create_index("ix_reference_entities_type", "reference_entities", ["ref_type"])


def upgrade() -> None:
    _create_crawl_sources()
    _create_knowledge_entities()
    _create_entity_enrichments()
    _create_change_events()
    _create_scholarships()
    _create_ref_occupations()
    _create_ref_tests()
    _create_ref_visas()
    _create_ref_geo_cost()
    _create_ref_majors()
    _create_ref_rankings()
    _create_ref_accreditation()
    _create_reference_entities()


def downgrade() -> None:
    for table in (
        "reference_entities",
        "ref_accreditation",
        "ref_rankings",
        "ref_majors",
        "ref_geo_cost",
        "ref_visas",
        "ref_tests",
        "ref_occupations",
        "scholarships",
        "change_events",
        "entity_enrichments",
        "knowledge_entities",
        "crawl_sources",
    ):
        if _has_table(table):
            op.drop_table(table)
