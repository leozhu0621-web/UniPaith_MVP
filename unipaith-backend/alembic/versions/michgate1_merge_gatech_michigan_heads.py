"""Merge Alembic heads gatechprof3 + michprof3 into a single head.

Revision ID: michgate1
Revises: gatechprof3, michprof3
Create Date: 2026-06-18
"""

from __future__ import annotations

revision = "michgate1"
down_revision = ("gatechprof3", "michprof3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
