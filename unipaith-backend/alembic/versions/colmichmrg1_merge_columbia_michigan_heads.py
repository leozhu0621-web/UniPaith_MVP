"""Merge the two concurrent alembic heads into one (merge-of-merges).

The auto-merge dual-head race produced two merge nodes on ``main``:
``colaivisamerge1`` (this session's Columbia + AI-visa head merge, #951) and
``michaimrg1`` (the concurrent AI-visa + Michigan head merge). A dual head fails
``test_alembic_has_single_head`` and blocks every backend deploy until unified. This is a
merge-only migration — no schema change; it joins the two merge heads so ``alembic upgrade
head`` is linear again.

Revision ID: colmichmrg1
Revises: colaivisamerge1, michaimrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "colmichmrg1"
down_revision = ("colaivisamerge1", "michaimrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
