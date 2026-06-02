"""Spec 56 §6 — Saved searches + alerts.

Adds ``saved_searches`` — the one net-new table Spec 56 calls for. A student
names a search/filter set; alert-enabled rows are re-run by the scheduled alert
loop, which notifies on new matches (Spec 56 §6, the proactive payoff that pairs
with Spec 60 §3B crawler freshness).

The table create is guarded (``_has_table``) so the migration is a safe no-op
against a dev/test DB built from the models via ``create_all`` (conftest path).

Revision ID: s56a1b2c3d4e
Revises: g46a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s56a1b2c3d4e"  # pragma: allowlist secret
# g46a1b2c3d4e (Spec 46 data-governance config) is the single head at branch
# time; chain off it to keep the graph single-headed (test_alembic_has_single_head).
down_revision = "g46a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table("saved_searches"):
        return
    op.create_table(
        "saved_searches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "entity_type",
            sa.String(length=20),
            nullable=False,
            server_default="program",
        ),
        sa.Column(
            "query",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "alert_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_match_count", sa.Integer(), nullable=True),
        sa.Column("last_alerted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "entity_type IN ('program', 'scholarship', 'school')",
            name="ck_saved_searches_entity_type",
        ),
    )
    op.create_index("ix_saved_searches_user_id", "saved_searches", ["user_id"])
    # Partial index — the alert loop only scans alert_enabled rows.
    op.create_index(
        "ix_saved_searches_alert_enabled",
        "saved_searches",
        ["alert_enabled"],
        postgresql_where=sa.text("alert_enabled"),
    )


def downgrade() -> None:
    if not _has_table("saved_searches"):
        return
    op.drop_index("ix_saved_searches_alert_enabled", table_name="saved_searches")
    op.drop_index("ix_saved_searches_user_id", table_name="saved_searches")
    op.drop_table("saved_searches")
