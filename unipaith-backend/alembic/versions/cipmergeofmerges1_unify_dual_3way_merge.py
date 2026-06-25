"""Merge-of-merges: unify the duplicate 3-way merge heads

Two sessions independently shipped a 3-way merge for the same berkeleycip2 +
vandycip1 + dartcipwho1 triple, and BOTH merged — so ``main`` now has two parallel
merge heads (the classic anti-fix-race outcome):
- ``berkvandydartmerge1`` (#1162)
- ``cip3waymerge1``        (#1161)

That dual head fails ``test_alembic_has_single_head`` and blocks every Deploy
Backend run. This empty merge-of-merges reunites the two into a single head so
deploys ship again.

Revision ID: cipmergeofmerges1
Revises: berkvandydartmerge1, cip3waymerge1
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "cipmergeofmerges1"
down_revision = ("berkvandydartmerge1", "cip3waymerge1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
