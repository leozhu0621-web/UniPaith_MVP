"""merge dual alembic heads: penntuition1 + gatechgradtuition1

Two graduate-tier tuition repairs (Penn ``penntuition1`` #1097 and Georgia Tech
``gatechgradtuition1`` #1091) both branched off ``harvardcip2`` and auto-merged to ``main``,
leaving two alembic heads. ``test_alembic_has_single_head`` fails and every Deploy Backend
``alembic upgrade head`` is blocked until the heads are unified. This is a merge-only
migration — no schema or data changes; it only joins the two lineages into one head.

Revision ID: penngatechmrg1
Revises: gatechgradtuition1, penntuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "penngatechmrg1"
down_revision = ("gatechgradtuition1", "penntuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge-only — no schema or data changes.
    pass


def downgrade() -> None:
    pass
