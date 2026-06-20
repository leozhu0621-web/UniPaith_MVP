"""Merge the headfix1 + uiucmrg1 dual head (anti-fix-race, merge-of-merges).

#908 (uiucmrg1) merged the jhuuscmrg1 + uiucprof5 pair; concurrently #910 (headfix1)
merged the SUPERSET jhuuscmrg1 + sesstmpl1 + uiucprof5. With both on main the two merge
migrations are siblings, leaving TWO heads (headfix1 + uiucmrg1) and a failing deploy.
This empty merge-of-merges unifies them into a single head.

Revision ID: uiucmrg2
Revises: headfix1, uiucmrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "uiucmrg2"
down_revision = ("headfix1", "uiucmrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
