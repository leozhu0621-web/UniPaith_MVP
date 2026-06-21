"""Merge deepintelmerge1 + nyurefmrg1 dual head before UCLA per-credential repair.

Revision ID: uclaheadmrg1
Revises: deepintelmerge1, nyurefmrg1
Create Date: 2026-06-21
"""

from __future__ import annotations

revision = "uclaheadmrg1"
down_revision = ("deepintelmerge1", "nyurefmrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
