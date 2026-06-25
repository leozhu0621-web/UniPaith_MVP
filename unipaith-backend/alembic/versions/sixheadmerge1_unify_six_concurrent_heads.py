"""Merge six concurrent alembic heads on origin/main (deploy pipeline unblock)

`origin/main` accumulated SIX divergent leaf-heads because parallel
single-head PRs each chained to the then-current head and squash-merged
(the squash-skew CLAUDE.md warns about). `alembic upgrade head` errors with
"Multiple head revisions are present", so NO new migration applies in prod
and merged enrichment repairs sit stranded NOT-LIVE (REPAIR_BACKLOG #1).

This merge-only migration unifies all six into one head. No schema or data
change.

Heads unified:
  a32revwork1b2c — spec32 review-assist agents
  b31a1c2d3e4f   — spec31 admissions intake
  dartfinish1    — dartmouth finish catalog cip/who
  deepintel1     — profile intelligence
  f1a9c0d2e3b4   — drop crawler tables
  n9p2q4r6s8t0   — spec03 audit-ledger fields

Revision ID: sixheadmerge1
Revises: a32revwork1b2c, b31a1c2d3e4f, dartfinish1, deepintel1, f1a9c0d2e3b4, n9p2q4r6s8t0
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "sixheadmerge1"
down_revision = (
    "a32revwork1b2c",
    "b31a1c2d3e4f",
    "dartfinish1",
    "deepintel1",
    "f1a9c0d2e3b4",
    "n9p2q4r6s8t0",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
