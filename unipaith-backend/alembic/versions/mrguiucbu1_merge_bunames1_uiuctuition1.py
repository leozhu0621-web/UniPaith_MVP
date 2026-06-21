"""Merge dual alembic heads: bunames1 + uiuctuition1.

Two enrichment repairs auto-merged off the same base (``uwmadtuition1``) — Boston
University real names (#1058, ``bunames1``) and the UIUC tuition backfill (#1061,
``uiuctuition1``) — leaving ``main`` with two heads. This empty merge migration
unifies them so ``test_alembic_has_single_head`` passes and Deploy Backend can run.

Revision ID: mrguiucbu1
Revises: bunames1, uiuctuition1
Create Date: 2026-06-21
"""

from __future__ import annotations

revision = "mrguiucbu1"
down_revision = ("bunames1", "uiuctuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
