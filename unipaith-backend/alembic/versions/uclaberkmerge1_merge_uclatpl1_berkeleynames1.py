"""Merge dual head: uclatpl1 + berkeleynames1.

#1027 (uclatpl1, via stanfordtuit1) and a concurrently-merged Berkeley names repair
(berkeleynames1) both descend from berkeleytpl2 and auto-merged into main against the
same base, leaving two alembic heads. This empty merge migration unifies them so
``alembic upgrade head`` is single-headed and Deploy Backend does not fail.

Revision ID: uclaberkmerge1
Revises: uclatpl1, berkeleynames1
Create Date: 2026-06-21
"""

from __future__ import annotations

revision = "uclaberkmerge1"
down_revision = ("uclatpl1", "berkeleynames1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
