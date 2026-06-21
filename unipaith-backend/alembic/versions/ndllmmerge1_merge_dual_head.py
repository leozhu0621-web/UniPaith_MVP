"""Merge dual alembic head: ndpercrd1 + utllmtuit1.

Notre Dame's per-credential repair (#1039, ``ndpercrd1``) and the UT Austin LL.M.
tuition fix (#1038, ``utllmtuit1``) both branched off ``utaustintuition1`` and
auto-merged, leaving ``main`` with two heads — which fails the single-head CI gate and
blocks Deploy Backend. This merge-only migration unifies them (no data changes).

Revision ID: ndllmmerge1
Revises: ndpercrd1, utllmtuit1
Create Date: 2026-06-21
"""

from __future__ import annotations

revision = "ndllmmerge1"
down_revision = ("ndpercrd1", "utllmtuit1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
