"""Merge harvardnames1 + coldukemerge1 Alembic heads.

PR #869 landed ``coldukemerge1`` (columbiadefab2 + dukedefab1) while PR #870 was
open with its own ``dukecolmerge1`` + ``harvardnames1`` chain — auto-merge left
two heads. Merge-only; no schema/data changes.

Revision ID: harvcoldukem1
Revises: coldukemerge1, harvardnames1
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "harvcoldukem1"
down_revision = ("coldukemerge1", "harvardnames1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
