"""Merge dual head again (casewestlehighmerge1 + lehighfix3) — merge-of-merges

The first merge migration (casewestlehighmerge1, unifying casewesttuition1 + lehighfix2)
raced with PR #1288 (lehighfix3, down_revision lehighfix2), which auto-merged just before
it. Because both casewestlehighmerge1 and lehighfix3 descend from lehighfix2, origin/main
was left with TWO heads again. This merge-of-merges unifies them into one linear head so
`test_alembic_has_single_head` passes and the backend deploy is unblocked. No data changes.

Revision ID: casewestlehighmerge2
Revises: casewestlehighmerge1, lehighfix3
Create Date: 2026-07-02
"""

from __future__ import annotations

revision = "casewestlehighmerge2"
down_revision = ("casewestlehighmerge1", "lehighfix3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
