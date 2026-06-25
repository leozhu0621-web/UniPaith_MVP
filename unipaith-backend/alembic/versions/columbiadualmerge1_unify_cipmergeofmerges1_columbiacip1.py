"""Unify the dual head left by the two duplicate merge-of-merges (empty merge)

`cipmergeofmerges1` (#1163) and `columbiacip1` (#1164) BOTH set their down_revision to
the same pair (`cip3waymerge1`, `berkvandydartmerge1`) and both auto-merged onto `main`,
leaving it dual-headed again — so `alembic upgrade head` is ambiguous,
`test_alembic_has_single_head` fails, and every Deploy Backend is blocked. This is an
empty merge-only migration (no schema/data change) that collapses the two into a single
head so deploys ship and the already-merged Columbia cip_code data can reach production.

Revision ID: columbiadualmerge1
Revises: cipmergeofmerges1, columbiacip1
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "columbiadualmerge1"
down_revision = ("cipmergeofmerges1", "columbiacip1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
