"""Merge dual head: jhucip2 + stanfordcipwho1.

The Stanford enrichment migration ``stanfordcipwho1`` and the JHU CIP-correction
``jhucip2`` both branched off ``jhucipwho1`` and auto-merged into ``main``
independently, leaving two alembic heads. This empty merge migration unifies them
so ``alembic upgrade head`` resolves to a single head and the backend deploy can run.
No data changes — both parents already applied their own upgrades.

Revision ID: stanfordmrg1
Revises: jhucip2, stanfordcipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

revision = "stanfordmrg1"
down_revision = ("jhucip2", "stanfordcipwho1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
