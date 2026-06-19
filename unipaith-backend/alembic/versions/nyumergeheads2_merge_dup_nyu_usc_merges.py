"""Merge the two duplicate NYU/USC head-merge migrations into one head.

Two sessions concurrently shipped a merge migration for the SAME head pair
(``nyuslugfix1`` + ``uscdefab1``): ``nyuuscheadsmerge1`` (#847) and ``nyuscmerge1``
(#846). Both auto-merged, so ``main`` is dual-headed again with the two sibling
merges. This empty merge-of-merges unifies them into a single head so
``test_alembic_has_single_head`` passes and the backend deploy stays unblocked.
No data change.

Revision ID: nyumergeheads2
Revises: nyuscmerge1, nyuuscheadsmerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "nyumergeheads2"
down_revision = ("nyuscmerge1", "nyuuscheadsmerge1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
