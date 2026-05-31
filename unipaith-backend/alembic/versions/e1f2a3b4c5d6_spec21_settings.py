"""Spec 21 — Settings: user_settings + institution_team_invites + notif email_frequency.

Adds the canonical per-user settings store (``user_settings``), the minimal
institution team/seats invite table (``institution_team_invites``), and an
``email_frequency`` column on ``notification_preferences``.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"  # pragma: allowlist secret
down_revision = "d0e1f2a3b4c5"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("photo_url", sa.String(length=1000), nullable=True),
        sa.Column("pending_email", sa.String(length=255), nullable=True),
        sa.Column("locale", sa.String(length=30), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        sa.Column("theme", sa.String(length=10), server_default="system", nullable=False),
        sa.Column("dyslexia_mode", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("font_size", sa.String(length=4), server_default="md", nullable=False),
        sa.Column("reduced_motion", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("mfa_method", sa.String(length=10), nullable=True),
        sa.Column("mfa_secret", sa.String(length=64), nullable=True),  # pragma: allowlist secret
        sa.Column(
            "mfa_pending_secret", sa.String(length=64), nullable=True
        ),  # pragma: allowlist secret
        sa.Column("mfa_recovery_codes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("deletion_scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_purge_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"])

    op.create_table(
        "institution_team_invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_institution_team_invites_institution_id",
        "institution_team_invites",
        ["institution_id"],
    )

    op.add_column(
        "notification_preferences",
        sa.Column("email_frequency", sa.String(length=20), server_default="all", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("notification_preferences", "email_frequency")
    op.drop_index(
        "ix_institution_team_invites_institution_id", table_name="institution_team_invites"
    )
    op.drop_table("institution_team_invites")
    op.drop_index("ix_user_settings_user_id", table_name="user_settings")
    op.drop_table("user_settings")
