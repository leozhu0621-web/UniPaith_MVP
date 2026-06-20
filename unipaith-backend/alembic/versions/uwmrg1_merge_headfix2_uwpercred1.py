"""Merge headfix2 + uwpercred1 (single Alembic head for deploy).

Revision ID: uwmrg1
Revises: headfix2, uwpercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "uwmrg1"
down_revision = ("headfix2", "uwpercred1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
