"""merge nwprof7 and 2a470cb3c0bd (USC merge) alembic heads

PR #759 (USC) and PR #760 (Northwestern) both branched off ``dukeprof6`` and
auto-merged, leaving ``main`` with two heads: ``nwprof7`` and the USC merge
``2a470cb3c0bd`` (uscprof3 + dukeprof6). This empty merge migration unifies them
so ``test_alembic_has_single_head`` passes and the backend deploy is unblocked.
No schema or data change.

Revision ID: nwuscmrg1
Revises: nwprof7, 2a470cb3c0bd
Create Date: 2026-06-18
"""

from __future__ import annotations

revision = "nwuscmrg1"
down_revision = ("nwprof7", "2a470cb3c0bd")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
