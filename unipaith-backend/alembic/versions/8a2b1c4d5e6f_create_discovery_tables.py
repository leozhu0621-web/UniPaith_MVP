"""Phase A — create discovery_sessions and discovery_messages.

Adds the storage backbone for the Stage 1 (Discovery) journey: track-segmented
sessions (profile / goals / needs) with append-only message logs. The Discovery
LLM (Plan 2) plugs into these tables; Phase A only ships the storage and CRUD
contracts so the UI rebuild in Phase B can proceed against real shapes.

Revision ID: 8a2b1c4d5e6f
Revises: 4c9d6e1a8b3f, 4c9e5f3a8b2d
Create Date: 2026-05-09 15:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "8a2b1c4d5e6f"  # pragma: allowlist secret
# Merge the two pre-existing heads in the same step. If the alembic graph is
# repaired separately (the duplicate m3n4o5p6q7r8 revision id needs untangling),
# this migration becomes the single new head.
down_revision = ("4c9d6e1a8b3f", "4c9e5f3a8b2d")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Allowed values: 'profile' | 'goals' | 'needs'
        sa.Column("track", sa.String(20), nullable=False),
        # Allowed values: 'basic' | 'personality' | 'identity' (only for track='profile')
        sa.Column("layer", sa.String(20), nullable=True),
        # Allowed values: 'active' | 'completed' | 'abandoned'
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column(
            "completion_pct",
            sa.Numeric(4, 3),
            nullable=False,
            server_default="0",
        ),
        sa.Column("exit_signal", postgresql.JSONB, nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "track IN ('profile','goals','needs')",
            name="ck_discovery_sessions_track",
        ),
        sa.CheckConstraint(
            "layer IS NULL OR layer IN ('basic','personality','identity')",
            name="ck_discovery_sessions_layer",
        ),
        sa.CheckConstraint(
            "status IN ('active','completed','abandoned')",
            name="ck_discovery_sessions_status",
        ),
        sa.CheckConstraint(
            "completion_pct >= 0 AND completion_pct <= 1",
            name="ck_discovery_sessions_completion_pct",
        ),
        sa.CheckConstraint(
            "(track = 'profile') OR (layer IS NULL)",
            name="ck_discovery_sessions_layer_only_for_profile",
        ),
    )
    op.create_index(
        "ix_discovery_sessions_student_track_status",
        "discovery_sessions",
        ["student_id", "track", "status"],
    )

    op.create_table(
        "discovery_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Allowed values: 'student' | 'assistant' | 'system'
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("extracted_signals", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('student','assistant','system')",
            name="ck_discovery_messages_role",
        ),
    )
    op.create_index(
        "ix_discovery_messages_session_created",
        "discovery_messages",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_discovery_messages_session_created", table_name="discovery_messages")
    op.drop_table("discovery_messages")
    op.drop_index("ix_discovery_sessions_student_track_status", table_name="discovery_sessions")
    op.drop_table("discovery_sessions")
