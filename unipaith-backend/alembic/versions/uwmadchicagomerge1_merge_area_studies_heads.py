"""Merge dual alembic head: chicagoareastudies1 + uwmadareastudies1

Two REPAIR_BACKLOG #1 "Area Studies" repairs (U-Chicago #1127 and UW-Madison #1129)
each branched off berkvandmerge1 and auto-merged, leaving origin/main with two heads.
Deploy Backend's `alembic upgrade head` fails on a dual head, so this merge-only
migration unifies them. No schema or data change.

Revision ID: uwmadchicagomerge1
Revises: chicagoareastudies1, uwmadareastudies1
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "uwmadchicagomerge1"
down_revision = ("chicagoareastudies1", "uwmadareastudies1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
