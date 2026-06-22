"""Merge harvardcipnames1 + ucsdgradtuition1 (dual-head auto-merge race)

Revision ID: harvarducsdmrg1
Revises: harvardcipnames1, ucsdgradtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "harvarducsdmrg1"
down_revision = ("harvardcipnames1", "ucsdgradtuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
