"""Merge the headfix2 + uiucbslas1 dual head (anti-fix-race).

#912 (uiucbslas1, down_revision=headfix1) and a concurrent merge migration
(headfix2 = headfix1 + uiucmrg1) both auto-merged off the same headfix1 base, leaving
``main`` with two alembic heads — which fails ``test_alembic_has_single_head`` and blocks
every backend deploy. This merge-only migration unifies them; empty upgrade/downgrade.

Revision ID: uiucheadmrg1
Revises: headfix2, uiucbslas1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "uiucheadmrg1"
down_revision = ("headfix2", "uiucbslas1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
