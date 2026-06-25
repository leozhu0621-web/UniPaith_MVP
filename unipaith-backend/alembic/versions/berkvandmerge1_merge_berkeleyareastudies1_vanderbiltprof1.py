"""Merge dual head: berkeleyareastudies1 + vanderbiltprof1.

#1123 (berkeleyareastudies1) and the concurrently-merged Vanderbilt enrichment
(vanderbiltprof1, #1121) both descend from brownprof1 and auto-merged into main
against the same base, leaving two alembic heads. This empty merge migration unifies
them so ``alembic upgrade head`` is single-headed and Deploy Backend does not fail.

Revision ID: berkvandmerge1
Revises: berkeleyareastudies1, vanderbiltprof1
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "berkvandmerge1"
down_revision = ("berkeleyareastudies1", "vanderbiltprof1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
