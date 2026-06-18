"""merge depadcu1 and nyuprof3 alembic heads

Revision ID: nyumrg1
Revises: depadcu1, nyuprof3
Create Date: 2026-06-18

"""

from __future__ import annotations

revision = "nyumrg1"
down_revision = ("depadcu1", "nyuprof3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
