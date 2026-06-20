"""Merge the two migration heads created by concurrent auto-merges: uwdefab1 (UW
description de-fabrication, #802) and seed3b6 (US-News seed batch 6, #813). Both
branched off a shared base and auto-merged, leaving main with a dual head that
blocks every deploy (test_alembic_has_single_head). Empty merge — no schema/data
change; it only unifies the heads.

Revision ID: uwseedmerge1
Revises: uwdefab1, seed3b6
Create Date: 2026-06-18
"""

from __future__ import annotations

revision = "uwseedmerge1"
down_revision = ("uwdefab1", "seed3b6")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
