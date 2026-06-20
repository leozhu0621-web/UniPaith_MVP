"""Merge buprof14 + promptcat1 Alembic heads.

Auto-merge race: PR #880 (buprof14) and #879 (promptcat1) both branched off nwdefab1.

Revision ID: bupromptmerge1
Revises: buprof14, promptcat1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "bupromptmerge1"
down_revision = ("buprof14", "promptcat1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
