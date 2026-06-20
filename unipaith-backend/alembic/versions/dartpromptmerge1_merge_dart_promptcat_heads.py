"""merge dartprof1 + promptcat2 alembic heads (data-only, no DDL)

Revision ID: dartpromptmerge1
Revises: dartprof1, promptcat2
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "dartpromptmerge1"
down_revision = ("dartprof1", "promptcat2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
