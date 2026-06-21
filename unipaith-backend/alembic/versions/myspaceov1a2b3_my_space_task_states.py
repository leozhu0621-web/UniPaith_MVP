"""My Space overview task presentation state.

Adds the small student-owned table used by the My Space overview to remember
computed-task dismissals and snoozes. True completion remains in the owning
domain tables.

Revision ID: myspaceov1a2b3
Revises: buprof10
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "myspaceov1a2b3"  # pragma: allowlist secret
down_revision = "buprof10"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _indexes(table: str) -> set[str]:
    if not _has_table(table):
        return set()
    return {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    if not _has_table("my_space_task_states"):
        op.create_table(
            "my_space_task_states",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("task_key", sa.String(length=180), nullable=False),
            sa.Column("dismissed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
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
            sa.ForeignKeyConstraint(
                ["student_id"],
                ["student_profiles.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "student_id",
                "task_key",
                name="uq_my_space_task_states_student_task",
            ),
        )
    existing = _indexes("my_space_task_states")
    if "ix_my_space_task_states_student_task" not in existing:
        op.create_index(
            "ix_my_space_task_states_student_task",
            "my_space_task_states",
            ["student_id", "task_key"],
        )
    if "ix_my_space_task_states_student_visibility" not in existing:
        op.create_index(
            "ix_my_space_task_states_student_visibility",
            "my_space_task_states",
            ["student_id", "dismissed", "snoozed_until"],
        )


def downgrade() -> None:
    if _has_table("my_space_task_states"):
        existing = _indexes("my_space_task_states")
        if "ix_my_space_task_states_student_visibility" in existing:
            op.drop_index(
                "ix_my_space_task_states_student_visibility",
                table_name="my_space_task_states",
            )
        if "ix_my_space_task_states_student_task" in existing:
            op.drop_index(
                "ix_my_space_task_states_student_task",
                table_name="my_space_task_states",
            )
        op.drop_table("my_space_task_states")
