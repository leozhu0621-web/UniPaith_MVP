"""Merge dual Alembic head: butuitionval1 + jhutuimrg1.

The auto-merge dual-head race (§8 step 5) recurred: ``butuitionval1`` (#1066, the BU tuition
value-correctness repair) and ``jhutuimrg1`` (#1063 fixup) BOTH merge the same
``(jhutuition1, mrguiucbu1)`` pair, so each was left as a head with no child. This is a
merge-only migration (empty upgrade/downgrade) that unifies the two into a single head.

Revision ID: bujhumrg1
Revises: butuitionval1, jhutuimrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "bujhumrg1"
down_revision = ("butuitionval1", "jhutuimrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
