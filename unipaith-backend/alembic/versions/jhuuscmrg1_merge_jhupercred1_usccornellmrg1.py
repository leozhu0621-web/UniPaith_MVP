"""Merge the jhupercred1 + usccornellmrg1 dual head (anti-fix-race)

Two sessions independently merged the same ``cornellpercred1`` + ``uscdebris2``
pair: ``jhupercred1`` (#901) set ``down_revision = (cornellpercred1, uscdebris2)``
while ``usccornellmrg1`` (#900) set ``down_revision = (uscdebris2, cornellpercred1)``.
Both auto-merged, so ``main`` is left with a dual head again (SKILL §8 step 3
anti-fix-race). This is an empty merge-of-merges that unifies them into a single
head; no data changes.

Revision ID: jhuuscmrg1
Revises: jhupercred1, usccornellmrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "jhuuscmrg1"
down_revision = ("jhupercred1", "usccornellmrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
