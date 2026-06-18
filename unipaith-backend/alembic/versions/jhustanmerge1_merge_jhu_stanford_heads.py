"""Merge jhudefab1 and stanfordprof10 migration heads.

Revision ID: jhustanmerge1
Revises: jhudefab1, stanfordprof10
Create Date: 2026-06-18
"""

from __future__ import annotations

revision = "jhustanmerge1"
down_revision = ("jhudefab1", "stanfordprof10")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
