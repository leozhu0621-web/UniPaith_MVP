"""Merge the uiucuwmrg1 + runnermrg1 dual head (merge-of-merges, anti-fix-race).

#921 (uiucuwmrg1 = merge uiucheadmrg1 + uwmrg1) and #922 (runnermrg1 = merge of the same
uiucheadmrg1 + uwmrg1 pair plus the chat-template-runner migration) both auto-merged off the
same base, leaving them as sibling heads on ``main`` — which fails
``test_alembic_has_single_head`` and blocks every backend deploy (including the deploy that
applies the UIUC de-roll-up from #912). This merge-only migration unifies them; empty
upgrade/downgrade.

Revision ID: uiucrunnermrg1
Revises: uiucuwmrg1, runnermrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "uiucrunnermrg1"
down_revision = ("uiucuwmrg1", "runnermrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
