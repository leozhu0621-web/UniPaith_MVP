"""merge the two duplicate feedsbackfill1+pennprof3 merge-heads

Two parallel sessions each added an (identical, empty) alembic merge of
``feedsbackfill1`` + ``pennprof3`` — ``mergepf3fb1`` and ``feedspennmerge1`` — and both
landed on ``main``, leaving two heads again. This empty merge migration unifies those two
duplicate merges into a single head so ``alembic upgrade head`` resolves and the
single-head compliance check passes. No schema or data changes.

Revision ID: mergeheads2
Revises: feedspennmerge1, mergepf3fb1
Create Date: 2026-06-10
"""

from __future__ import annotations

revision = "mergeheads2"
down_revision = ("feedspennmerge1", "mergepf3fb1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Empty merge — unifies two duplicate merge-heads into one.
    pass


def downgrade() -> None:
    # Nothing structural to roll back.
    pass
