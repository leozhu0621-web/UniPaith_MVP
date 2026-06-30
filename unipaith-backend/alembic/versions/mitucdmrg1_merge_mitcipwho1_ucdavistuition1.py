"""Merge the two heads created by concurrent auto-merges (mitcipwho1 + ucdavistuition1).

Both #1231 (``mitcipwho1`` — MIT cip_code / who_its_for) and #1232
(``ucdavistuition1`` — UC Davis M.B.A./M.P.H. tuition) branched off the same base
(``gtowntuition3``) and auto-merged on green CI, leaving ``main`` with two alembic
heads. This empty merge migration unifies them so ``test_alembic_has_single_head``
passes and Deploy Backend can apply the chain to production.

No data changes — both parent migrations already carry their own data apply.

Revision ID: mitucdmrg1
Revises: mitcipwho1, ucdavistuition1
Create Date: 2026-06-30
"""

from __future__ import annotations

revision = "mitucdmrg1"
down_revision = ("mitcipwho1", "ucdavistuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
