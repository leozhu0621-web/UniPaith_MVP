"""Merge the uiucheadmrg1 + uwmrg1 dual head (merge-of-merges, anti-fix-race).

#918 (uiucheadmrg1 = merge headfix2 + uiucbslas1) and #914 (uwmrg1 = merge headfix2 +
uwpercred1) both auto-merged off the same headfix2 base, leaving ``main`` with two alembic
heads — which fails ``test_alembic_has_single_head`` and blocks every backend deploy. This
merge-only migration unifies them; empty upgrade/downgrade.

Revision ID: uiucuwmrg1
Revises: uiucheadmrg1, uwmrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "uiucuwmrg1"
down_revision = ("uiucheadmrg1", "uwmrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
