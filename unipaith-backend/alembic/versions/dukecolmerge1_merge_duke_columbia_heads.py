"""Merge dukedefab1 + columbiadefab2 Alembic heads.

Both branched from colyalemerge1 when Duke (#868) and Columbia (#866) landed
concurrently; unifies to a single head before the Harvard possessive-name repair.

Revision ID: dukecolmerge1
Revises: columbiadefab2, dukedefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "dukecolmerge1"
down_revision = ("columbiadefab2", "dukedefab1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
