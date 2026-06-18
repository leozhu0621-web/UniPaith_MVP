"""Merge alembic heads seed12univ1 + ucsdprof7

Revision ID: ucsdseedmerge1
Revises: seed12univ1, ucsdprof7
Create Date: 2026-06-18
"""

from __future__ import annotations

revision = "ucsdseedmerge1"
down_revision = ("seed12univ1", "ucsdprof7")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
