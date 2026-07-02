"""Merge dual alembic head from concurrent auto-merges (casewesttuition1 + lehighfix2)

Two enrichment PRs auto-merged off the same base (`lehighfix1`): #1286
(`casewesttuition1`, Case Western tuition fills) and #1287 (`lehighfix2`, Lehigh
graduate-load / Ed.D. fixes). Each read single-head against its own base and passed CI,
but together they left `origin/main` with TWO heads — which fails
`test_alembic_has_single_head` and blocks every backend deploy. This merge-only
migration unifies them into one head so the chain is linear again. No data changes.

Revision ID: casewestlehighmerge1
Revises: casewesttuition1, lehighfix2
Create Date: 2026-07-02
"""

from __future__ import annotations

revision = "casewestlehighmerge1"
down_revision = ("casewesttuition1", "lehighfix2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
