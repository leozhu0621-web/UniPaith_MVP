"""merge dual alembic heads: harvardnames3 + ndgradtuition1

Two repairs (Harvard ``harvardnames3`` #1103 un-doubling professional-degree names
and Notre Dame ``ndgradtuition1`` #1105 graduate-tier tuition) both branched off
``yalegradtuition1`` and auto-merged to ``main``, leaving two alembic heads.
``test_alembic_has_single_head`` fails and every Deploy Backend ``alembic upgrade head``
errors ``Multiple head revisions present`` until the heads are unified. This is a
merge-only migration — no schema or data changes; it only joins the two lineages into
one head so deploys can resume.

Revision ID: harvardndmrg1
Revises: harvardnames3, ndgradtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "harvardndmrg1"
down_revision = ("harvardnames3", "ndgradtuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge-only — no schema or data changes.
    pass


def downgrade() -> None:
    pass
