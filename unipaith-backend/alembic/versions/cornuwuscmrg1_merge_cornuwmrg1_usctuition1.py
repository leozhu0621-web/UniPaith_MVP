"""Merge-of-merges: cornuwmrg1 + usctuition1 (double auto-merge race).

The cornellphdtui1+uwtuition1 dual head was merged TWICE concurrently — by cornuwmrg1
(#1076, this session) and by usccornuwmerge1 (#1078, the USC session, which then stacked
usctuition1 on it). main therefore split into two heads again: cornuwmrg1 and usctuition1.
This empty merge-of-merges unifies them so test_alembic_has_single_head passes and Deploy
Backend can run. No schema/data change.

Revision ID: cornuwuscmrg1
Revises: cornuwmrg1, usctuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "cornuwuscmrg1"
down_revision = ("cornuwmrg1", "usctuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
