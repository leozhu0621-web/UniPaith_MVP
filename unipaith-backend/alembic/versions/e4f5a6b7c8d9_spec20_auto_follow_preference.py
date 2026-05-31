"""Spec 20 §2 — auto-follow on save preference.

Adds ``auto_follow_on_save`` to ``student_preferences`` (default true).
When false, saving a program does not create an institution follow and saved
programs no longer implicitly scope the Connect feed.

Revision ID: e4f5a6b7c8d9
Revises: c20c7a1f9e30
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "e4f5a6b7c8d9"  # pragma: allowlist secret
down_revision = "c20c7a1f9e30"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "student_preferences", "auto_follow_on_save"):
        op.add_column(
            "student_preferences",
            sa.Column(
                "auto_follow_on_save",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "student_preferences", "auto_follow_on_save"):
        op.drop_column("student_preferences", "auto_follow_on_save")
