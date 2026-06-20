"""Merge the nyuprof4 + uiucuwmrg1 dual head (merge-of-merges, anti-fix-race).

#920 (nyuprof4 = NYU CRITICAL #2 repair, chained off runnermrg1) and #921 (uiucuwmrg1 =
merge of uiucheadmrg1 + uwmrg1) left ``main`` with two alembic heads — which fails
``test_alembic_has_single_head`` and blocks every backend deploy (including the NYU repair
this run just landed and the #912 UIUC de-roll-up). This merge-only migration unifies them
so the deploy can proceed; empty upgrade/downgrade. Supersedes the open #924
(uiucrunnermrg1), whose uiucuwmrg1 + runnermrg1 pair is fully covered here (runnermrg1 is an
ancestor of nyuprof4).

Revision ID: nyuheadmrg1
Revises: nyuprof4, uiucuwmrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "nyuheadmrg1"
down_revision = ("nyuprof4", "uiucuwmrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
