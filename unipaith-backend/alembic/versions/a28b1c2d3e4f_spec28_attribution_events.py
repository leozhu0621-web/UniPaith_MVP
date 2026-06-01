"""Spec 28 — Attribution & Funnel Analytics: the ``attribution_events`` store.

Adds the canonical event-sourced table (spec §8) the analytics module reads
aggregate from. Chains onto main's single head (``f27e5a1c0d34`` Spec 27),
keeping a single linear head (``test_alembic_has_single_head``).

``create_table`` is guarded with ``_has_table`` so the revision is a safe no-op
against a dev/test DB built from the models via ``create_all``.

Revision ID: a28b1c2d3e4f
Revises: f27e5a1c0d34
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "a28b1c2d3e4f"  # pragma: allowlist secret
down_revision = "f27e5a1c0d34"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        return table in set(insp.get_table_names())
    except Exception:
        return False


def upgrade() -> None:
    if _has_table("attribution_events"):
        return

    op.create_table(
        "attribution_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_kind", sa.String(length=30), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intake_round_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dedupe_key", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["intake_round_id"], ["intake_rounds.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["segment_id"], ["target_segments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key"),
    )
    op.create_index(
        "ix_attribution_events_institution_id", "attribution_events", ["institution_id"]
    )
    op.create_index(
        "ix_attribution_inst_occurred",
        "attribution_events",
        ["institution_id", "occurred_at"],
    )
    op.create_index(
        "ix_attribution_inst_action", "attribution_events", ["institution_id", "action"]
    )
    op.create_index(
        "ix_attribution_inst_source",
        "attribution_events",
        ["institution_id", "source_kind", "source_id"],
    )
    op.create_index(
        "ix_attribution_inst_campaign",
        "attribution_events",
        ["institution_id", "campaign_id"],
    )
    op.create_index(
        "ix_attribution_inst_program",
        "attribution_events",
        ["institution_id", "program_id"],
    )


def downgrade() -> None:
    if not _has_table("attribution_events"):
        return
    op.drop_table("attribution_events")
