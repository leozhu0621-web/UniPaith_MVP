"""Add engine_loop_snapshot singleton for durable engine tick stats.

Revision ID: e5f1a2b3c904
Revises: d4e8a2b1c901
Create Date: 2026-04-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f1a2b3c904"
down_revision: str | None = "d4e8a2b1c901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engine_loop_snapshot",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_tick_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_bootstrap_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frontier_pending_before", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frontier_pending_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("batch_was_empty", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("tick_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("cumulative_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cumulative_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_mock_mode", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("gpu_mode", sa.String(length=20), nullable=False, server_default="openai"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("engine_loop_snapshot")
