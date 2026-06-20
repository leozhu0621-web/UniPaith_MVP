"""Merge the two concurrent alembic heads into one.

Two enrichment / feature PRs auto-merged off the same base and left ``main`` with a dual
head: ``columbiapercred1`` (Columbia per-credential descriptions, #942) and
``aivisamerge1`` (the match typed-fit migration slice, #829). A dual head fails
``test_alembic_has_single_head`` and blocks every backend deploy until unified. This is a
merge-only migration — no schema change; it simply joins the two heads so ``alembic
upgrade head`` is linear again.

Revision ID: colaivisamerge1
Revises: columbiapercred1, aivisamerge1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "colaivisamerge1"
down_revision = ("columbiapercred1", "aivisamerge1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
