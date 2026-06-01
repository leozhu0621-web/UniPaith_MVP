"""Spec 26 (Audience Segmentation): rule tree, uploaded lists, NL-bridge agent.

This revision does two things:

1. **Extends ``target_segments``** with the Spec 26 §7 ``Segment`` shape — a
   nested include/exclude ``rules`` tree (superseding the legacy flat
   ``criteria``), plus the author and a cached preview count. (Spec 25 already
   added ``description`` / ``uploaded_list_ids`` / ``frequency_cap_per_week``;
   those adds here are guarded no-ops.)
2. **Widens ``ck_ai_turns_agent``** to admit the new ``segment_builder_nl`` agent
   (Spec 26 §6 / 45 §17), keeping Spec 25's ``campaign_copy``.

Chains off ``e9f0a1b2c3d4`` (the Spec 24/25 merge head) so the graph stays a
single linear head (``test_alembic_has_single_head``). All operations are
guarded with ``_has_table`` / ``_has_column`` so the revision is a safe no-op
against a dev/test DB built from the models via ``create_all``.

Revision ID: a26d5e9f1b3c
Revises: e9f0a1b2c3d4
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "a26d5e9f1b3c"  # pragma: allowlist secret
down_revision = "e9f0a1b2c3d4"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Current vocabulary (post Spec 24/25) + the new segment_builder_nl agent.
_AGENT_CHECK_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl')"
)
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage')"
)


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {c["name"] for c in _inspector().get_columns(table)}


def upgrade() -> None:
    # ── 1. extend target_segments with the Spec 26 §7 shape ──────────────
    if _has_table("target_segments"):
        if not _has_column("target_segments", "description"):
            op.add_column("target_segments", sa.Column("description", sa.Text(), nullable=True))
        if not _has_column("target_segments", "rules"):
            op.add_column("target_segments", sa.Column("rules", postgresql.JSONB(), nullable=True))
        if not _has_column("target_segments", "uploaded_list_ids"):
            op.add_column(
                "target_segments",
                sa.Column(
                    "uploaded_list_ids",
                    postgresql.JSONB(),
                    nullable=False,
                    server_default=sa.text("'[]'::jsonb"),
                ),
            )
        if not _has_column("target_segments", "frequency_cap_per_week"):
            op.add_column(
                "target_segments",
                sa.Column("frequency_cap_per_week", sa.Integer(), nullable=True),
            )
        if not _has_column("target_segments", "created_by_user_id"):
            op.add_column(
                "target_segments",
                sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                "fk_target_segments_created_by_user",
                "target_segments",
                "users",
                ["created_by_user_id"],
                ["id"],
                ondelete="SET NULL",
            )
        if not _has_column("target_segments", "preview_audience_count"):
            op.add_column(
                "target_segments",
                sa.Column("preview_audience_count", sa.Integer(), nullable=True),
            )
        if not _has_column("target_segments", "preview_generated_at"):
            op.add_column(
                "target_segments",
                sa.Column("preview_generated_at", sa.DateTime(timezone=True), nullable=True),
            )

    # ── 2. widen ck_ai_turns_agent for segment_builder_nl ────────────────
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

    if _has_table("target_segments"):
        if _has_column("target_segments", "created_by_user_id"):
            op.drop_constraint(
                "fk_target_segments_created_by_user", "target_segments", type_="foreignkey"
            )
        for col in (
            "preview_generated_at",
            "preview_audience_count",
            "created_by_user_id",
            "frequency_cap_per_week",
            "uploaded_list_ids",
            "rules",
            "description",
        ):
            if _has_column("target_segments", col):
                op.drop_column("target_segments", col)
