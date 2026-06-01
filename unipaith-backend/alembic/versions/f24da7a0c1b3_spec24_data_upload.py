"""Spec 24 (Data Upload): dataset versioning, mapping templates, coverage range.

This revision does three things:

1. **Unifies the open heads** by descending from main's two leaves
   (``c9d8e7f6a5b4`` spec-21 review_config and ``d1e2f3a4b5c6`` spec-22 contact
   phone), restoring the ``test_alembic_has_single_head`` invariant.
2. **Extends ``institution_datasets``** with the coverage range, normalization
   map, and aligns the ``status`` vocabulary to the spec
   (``uploaded → validated → processed → failed``).
3. **Adds ``dataset_versions``** (Spec 24 §6 — per-write snapshots + rollback)
   and ``dataset_mapping_templates`` (Spec 24 §4.5/§12 — reusable column maps).

It also widens ``ck_ai_turns_agent`` to admit the new ``document_parse_triage``
agent (Spec 24 §9 / 45 §19).

All operations are guarded with ``_has_table`` / ``_has_column`` so the revision
is a safe no-op against a dev/test DB that was built from the models via
``create_all``.

Revision ID: f24da7a0c1b3
Revises: c9d8e7f6a5b4, d1e2f3a4b5c6
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f24da7a0c1b3"  # pragma: allowlist secret
down_revision = ("c9d8e7f6a5b4", "d1e2f3a4b5c6")  # pragma: allowlist secret
branch_labels = None
depends_on = None


_AGENT_CHECK = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'document_parse_triage')"
)
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender')"
)


def _has_table(bind, table: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return insp.has_table(table)
    except Exception:
        return False


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. institution_datasets: coverage range + normalization map ──────
    if _has_table(bind, "institution_datasets"):
        if not _has_column(bind, "institution_datasets", "coverage_start"):
            op.add_column(
                "institution_datasets", sa.Column("coverage_start", sa.Date(), nullable=True)
            )
        if not _has_column(bind, "institution_datasets", "coverage_end"):
            op.add_column(
                "institution_datasets", sa.Column("coverage_end", sa.Date(), nullable=True)
            )
        if not _has_column(bind, "institution_datasets", "normalization_map"):
            op.add_column(
                "institution_datasets",
                sa.Column("normalization_map", postgresql.JSONB(), nullable=True),
            )
        # Align legacy status vocab to the spec lifecycle.
        op.execute("UPDATE institution_datasets SET status='uploaded' WHERE status='pending'")
        op.execute("UPDATE institution_datasets SET status='processed' WHERE status='active'")

    # ── 2. dataset_versions ──────────────────────────────────────────────
    if not _has_table(bind, "dataset_versions"):
        op.create_table(
            "dataset_versions",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "dataset_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institution_datasets.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("s3_key", sa.String(length=1000), nullable=False),
            sa.Column("row_count", sa.Integer(), nullable=True),
            sa.Column("changes_summary", postgresql.JSONB(), nullable=True),
            sa.Column("validation_report", postgresql.JSONB(), nullable=True),
            sa.Column(
                "uploaded_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "uploaded_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint("dataset_id", "version_number", name="uq_dataset_version_number"),
        )
        op.create_index("ix_dataset_versions_dataset", "dataset_versions", ["dataset_id"])

    # ── 3. dataset_mapping_templates ─────────────────────────────────────
    if not _has_table(bind, "dataset_mapping_templates"):
        op.create_table(
            "dataset_mapping_templates",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("dataset_type", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("column_mapping", postgresql.JSONB(), nullable=False),
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
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
            sa.UniqueConstraint(
                "institution_id", "dataset_type", "name", name="uq_mapping_template_name"
            ),
        )
        op.create_index(
            "ix_mapping_templates_inst_type",
            "dataset_mapping_templates",
            ["institution_id", "dataset_type"],
        )

    # ── 4. widen ck_ai_turns_agent for document_parse_triage ─────────────
    if _has_table(bind, "ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_AGENT_CHECK})")


def downgrade() -> None:
    bind = op.get_bind()

    if _has_table(bind, "ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        op.execute(
            f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_AGENT_CHECK_OLD})"
        )

    if _has_table(bind, "dataset_mapping_templates"):
        op.drop_index("ix_mapping_templates_inst_type", table_name="dataset_mapping_templates")
        op.drop_table("dataset_mapping_templates")

    if _has_table(bind, "dataset_versions"):
        op.drop_index("ix_dataset_versions_dataset", table_name="dataset_versions")
        op.drop_table("dataset_versions")

    if _has_table(bind, "institution_datasets"):
        for col in ("normalization_map", "coverage_end", "coverage_start"):
            if _has_column(bind, "institution_datasets", col):
                op.drop_column("institution_datasets", col)
