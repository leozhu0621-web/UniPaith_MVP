"""Merge dual Alembic head: bujhumrg1 + cornelltuition1.

The auto-merge dual-head race (§8 step 5) recurred again: ``bujhumrg1`` (#1067) and
``cornelltuition1`` (#1068, the Cornell tuition repair) BOTH merge the same
``(butuitionval1, jhutuimrg1)`` pair, so each was left as a head with no child. This
merge-only migration (empty upgrade/downgrade) unifies the two into a single head.

Revision ID: bucornmrg1
Revises: bujhumrg1, cornelltuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "bucornmrg1"
down_revision = ("bujhumrg1", "cornelltuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
