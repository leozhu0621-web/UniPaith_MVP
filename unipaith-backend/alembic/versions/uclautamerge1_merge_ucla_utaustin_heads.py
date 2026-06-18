"""Merge the UCLA (uclaprof3) and UT Austin (utaprof2) Alembic heads.

Both de-fabrication migrations branched off michgate1 concurrently, producing a
dual head. This merge-only migration unifies them into a single head (no schema
or data changes).

Revision ID: uclautamerge1
Revises: uclaprof3, utaprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

revision = "uclautamerge1"
down_revision = ("uclaprof3", "utaprof2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
