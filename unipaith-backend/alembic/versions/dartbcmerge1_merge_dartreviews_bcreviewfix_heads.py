"""Merge the two heads created by concurrent auto-merges (bcreviewfix1 + dartreviews1).

PR #1258 (bcreviewfix1) and PR #1259 (dartreviews1) both branched off the same base
(bcgradtuition1) and both auto-merged on green CI, leaving origin/main with a DUAL head.
``test_alembic_has_single_head`` fails and every backend deploy is blocked until the two
heads are unified. This is an empty merge-only migration (no data changes) whose sole job
is to re-single the alembic chain.

Revision ID: dartbcmerge1
Revises: bcreviewfix1, dartreviews1
Create Date: 2026-07-01
"""

from __future__ import annotations

revision = "dartbcmerge1"
down_revision = ("bcreviewfix1", "dartreviews1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
