"""Merge jhutuition1 and mrguiucbu1 Alembic heads.

PR #1062 landed mrguiucbu1 (bunames1 + uiuctuition1) while #1063 landed jhubumrg1
(duplicate merge) + jhutuition1, leaving two heads that block deploy.

Revision ID: jhutuimrg1
Revises: jhutuition1, mrguiucbu1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "jhutuimrg1"
down_revision = ("jhutuition1", "mrguiucbu1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
