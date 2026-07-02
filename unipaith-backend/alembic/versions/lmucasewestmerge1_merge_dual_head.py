"""Merge dual alembic head from concurrent auto-merges (casewestfix1 + lmutuition1)

Two enrichment PRs auto-merged off the same base (casewestprof1): #1278
(casewestfix1, Case Western Codex correctness re-apply) and #1279 (lmutuition1,
LMU graduate-tuition fill). Both set down_revision = casewestprof1, so the merged
main carried TWO heads — which fails test_alembic_has_single_head and blocks the
backend deploy. This is a merge-only migration (no data changes) that unifies them.

Revision ID: lmucasewestmerge1
Revises: casewestfix1, lmutuition1
Create Date: 2026-07-02
"""

from __future__ import annotations

revision = "lmucasewestmerge1"
down_revision = ("casewestfix1", "lmutuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
