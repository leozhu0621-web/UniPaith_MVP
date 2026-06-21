"""Merge the nyugold1 + refinst01institutions dual head.

Two sessions concurrently merged the same colaivisamerge1 + michaimrg1 pair: this
branch's ``nyugold1`` (NYU gold repair) and ``colmichmrg1`` (which ``refinst01institutions``
then built on). Both auto-merged on green CI, leaving ``main`` with two heads
(``nyugold1`` and ``refinst01institutions``) and a blocked Deploy Backend. This
merge-only migration (no upgrade/downgrade body) unifies them back to a single head.

Revision ID: nyurefmrg1
Revises: nyugold1, refinst01institutions
Create Date: 2026-06-21
"""

from __future__ import annotations

revision = "nyurefmrg1"
down_revision = ("nyugold1", "refinst01institutions")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
