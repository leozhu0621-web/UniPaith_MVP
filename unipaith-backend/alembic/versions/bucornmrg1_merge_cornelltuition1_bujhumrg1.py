"""Merge dual Alembic head: cornelltuition1 + bujhumrg1.

The auto-merge dual-head race (§8 step 5) recurred a second time on the same parents.
``cornelltuition1`` (#1068, the Cornell tuition value-correctness repair) and ``bujhumrg1``
(#1067, the BU dual-head fixup) BOTH descend from the same ``(butuitionval1, jhutuimrg1)``
pair — #1068 carried the Cornell data AND merged the pair, while #1067 merged the same pair
as a standalone fixup — so each was left as a head with no child, leaving two heads on
``main``. ``test_alembic_has_single_head`` fails and Deploy Backend is blocked (so the BU
#1066 and Cornell #1068 tuition repairs cannot reach production) until this lands.

This is a merge-only migration (empty upgrade/downgrade) that unifies the two heads into a
single head ``bucornmrg1``. No schema or data change.

Revision ID: bucornmrg1
Revises: cornelltuition1, bujhumrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "bucornmrg1"
down_revision = ("cornelltuition1", "bujhumrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
