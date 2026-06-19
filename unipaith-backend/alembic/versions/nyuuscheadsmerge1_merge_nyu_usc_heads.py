"""Merge dual migration heads from concurrent auto-merges (nyuslugfix1 + uscdefab1).

#845 (``nyuslugfix1``, NYU slug-leak repair) and #843 (``uscdefab1``, USC
concentration-split collapse) both branched off ``uscprof4`` and auto-merged on green
CI, leaving ``main`` with two heads. This empty merge-only migration unifies them into a
single head so ``test_alembic_has_single_head`` passes and the backend deploy stays
unblocked. No data change.

Revision ID: nyuuscheadsmerge1
Revises: nyuslugfix1, uscdefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "nyuuscheadsmerge1"
down_revision = ("nyuslugfix1", "uscdefab1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
