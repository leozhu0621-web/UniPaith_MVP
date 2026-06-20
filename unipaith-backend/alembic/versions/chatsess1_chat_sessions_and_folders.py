"""chat_folders + chat_sessions (Uni chat-tab sessions model)

Hand-written; autogenerate is unreliable (env.py runs create_all).

Revision ID: chatsess1
Revises: pennnames1
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "chatsess1"  # pragma: allowlist secret
down_revision: str | None = "pennnames1"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _has("chat_folders"):
        op.create_table(
            "chat_folders",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("kind", sa.String(length=10), server_default="custom", nullable=False),
            sa.Column("topic_key", sa.String(length=30), nullable=True),
            sa.Column("stage", sa.String(length=20), nullable=True),
            sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
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
            sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint("kind IN ('preset','custom')", name="ck_chat_folders_kind"),
            sa.CheckConstraint(
                "(kind = 'preset') = (topic_key IS NOT NULL)",
                name="ck_chat_folders_preset_has_topic",
            ),
            sa.UniqueConstraint("student_id", "topic_key", name="uq_chat_folders_student_topic"),
        )
        op.create_index(
            "ix_chat_folders_student_sort", "chat_folders", ["student_id", "sort_order"]
        )
    if not _has("chat_sessions"):
        op.create_table(
            "chat_sessions",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
            sa.Column("origin_kind", sa.String(length=30), server_default="manual", nullable=False),
            sa.Column("origin_ref", sa.String(length=255), nullable=True),
            sa.Column("agent_session_id", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=12), server_default="active", nullable=False),
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
            sa.Column(
                "last_activity_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["folder_id"], ["chat_folders.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.CheckConstraint("status IN ('active','archived')", name="ck_chat_sessions_status"),
        )
        op.create_index(
            "ix_chat_sessions_folder_sort", "chat_sessions", ["folder_id", "sort_order"]
        )
        op.create_index(
            "ix_chat_sessions_student_pinned", "chat_sessions", ["student_id", "pinned"]
        )


def downgrade() -> None:
    op.drop_table("chat_sessions")
    op.drop_table("chat_folders")
