"""Merge the 3-way alembic head: berkeleycip2 + dartcipwho1 + vandycip1

Three matcher-core cip_code enrichment PRs (Berkeley #1156, Dartmouth #1159,
Vanderbilt #1155) each branched off the SAME base (berkeleycip1) and auto-merged on
green CI, leaving ``main`` with THREE heads. ``alembic upgrade head`` fails on multiple
heads, so the prod Deploy Backend is blocked until they are unified. This is a merge-only
migration (no schema/data change) collapsing all three into a single head.

Revision ID: cip3waymerge1
Revises: berkeleycip2, dartcipwho1, vandycip1
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "cip3waymerge1"
down_revision = ("berkeleycip2", "dartcipwho1", "vandycip1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
