"""merge uscdebris2 + cornellpercred1 heads

Two enrichment migrations auto-merged off the same base (uscdebris2 + the racing
cornellpercred1), leaving main with a dual head. This empty merge migration unifies
them so `alembic upgrade head` resolves to one head and deploys stay unblocked.

Revision ID: usccornellmrg1
Revises: uscdebris2, cornellpercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "usccornellmrg1"
down_revision = ("uscdebris2", "cornellpercred1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
