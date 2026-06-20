"""Merge the jhuuscmrg1 + uiucprof5 dual head (anti-fix-race).

#907 restored the lost jhuuscmrg1 merge migration (which uwmadpercred2 had referenced)
while, concurrently, #906 fixed the same breakage the OTHER way — re-pointing
uwmadpercred2's down_revision from jhuuscmrg1 to jhupercred1. With #906 merged first,
the restored jhuuscmrg1 became an orphaned leaf, so after #907 squashed onto main the
tree carried TWO heads (jhuuscmrg1 + uiucprof5) and every deploy fails on the multiple-
head error. This empty merge-only migration unifies them into a single head; it is safe
whether or not jhuuscmrg1 was ever stamped in a given environment.

Revision ID: uiucmrg1
Revises: jhuuscmrg1, uiucprof5
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "uiucmrg1"
down_revision = ("jhuuscmrg1", "uiucprof5")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
