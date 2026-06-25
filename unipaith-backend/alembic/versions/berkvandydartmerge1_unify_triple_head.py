"""Unify the triple alembic head (berkeleycip2 + vandycip1 + dartcipwho1)

Three enrichment PRs branched off the SAME base ``berkeleycip1`` and auto-merged
concurrently, each adding a sibling head:
- ``berkeleycip2``  (#1156 — Berkeley cip/tuition re-apply)
- ``vandycip1``     (#1155 — Vanderbilt cip + grad tuition + reviews)
- ``dartcipwho1``   (#1159 — Dartmouth cip + who_its_for)

A multi-head ``main`` fails ``test_alembic_has_single_head`` and blocks every
Deploy Backend run. This is an empty merge-only migration that reunites the three
heads into one so the chain is single-head again and deploys can ship.

Revision ID: berkvandydartmerge1
Revises: berkeleycip2, vandycip1, dartcipwho1
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "berkvandydartmerge1"
down_revision = ("berkeleycip2", "vandycip1", "dartcipwho1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
