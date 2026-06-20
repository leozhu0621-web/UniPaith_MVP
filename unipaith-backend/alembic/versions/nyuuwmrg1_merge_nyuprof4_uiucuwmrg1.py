"""Merge the nyuprof4 + uiucuwmrg1 dual head into a single head.

After #920 (`nyuprof4`) auto-merged off `runnermrg1` and #921 (`uiucuwmrg1`) auto-merged
off `uiucheadmrg1 + uwmrg1`, ``main`` carried two sibling heads. (The earlier open merge
#924 targets `uiucuwmrg1 + runnermrg1`, but `runnermrg1` is already an ancestor of
`nyuprof4`, so that merge would not unify the live heads.) This merge-only revision joins
the actual current heads so ``test_alembic_has_single_head`` passes and backend deploys
proceed. ``upgrade``/``downgrade`` are no-ops — graph repair only, no schema or data change.

Revision ID: nyuuwmrg1
Revises: nyuprof4, uiucuwmrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "nyuuwmrg1"
down_revision = ("nyuprof4", "uiucuwmrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
