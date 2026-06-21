"""Merge dual head: pennpercrd1 + uclajhurelay1 (enrich-profile §8 step 5).

``#1029`` (``pennpercrd1``) and ``#1031`` (``uclajhurelay1``) both descend from
``uclaberkmerge1`` and auto-merged into ``main`` against the same base, leaving two
alembic heads. ``test_alembic_has_single_head`` fails and future deploys' single-head
assertion blocks until the heads are unified.

Empty merge-only migration (no DDL / data) — both branches' upgrades have already run.
``alembic heads`` → single ``pennuclamerge1``.

Revision ID: pennuclamerge1
Revises: pennpercrd1, uclajhurelay1
Create Date: 2026-06-21
"""

from __future__ import annotations

revision = "pennuclamerge1"
down_revision = ("pennpercrd1", "uclajhurelay1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
