"""Merge bunames1 and uiuctuition1 Alembic heads.

Two enrichment PRs (#1058 bunames1, #1061 uiuctuition1) both branched off uwmadtuition1
and auto-merged, leaving main with a dual head that blocks deploy until unified.

Revision ID: jhubumrg1
Revises: bunames1, uiuctuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "jhubumrg1"
down_revision = ("bunames1", "uiuctuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
