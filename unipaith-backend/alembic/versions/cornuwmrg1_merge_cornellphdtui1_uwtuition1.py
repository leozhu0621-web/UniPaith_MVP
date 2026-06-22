"""Merge dual Alembic head: cornellphdtui1 + uwtuition1 (auto-merge race).

Cornell PhD-tuition (#1071, cornellphdtui1) and UW-Seattle tuition (#1074, uwtuition1)
both branched off cmutuition1 and both auto-merged on green CI, leaving main with two
heads. This empty merge migration unifies them so test_alembic_has_single_head passes and
Deploy Backend can run. No schema/data change.

Revision ID: cornuwmrg1
Revises: cornellphdtui1, uwtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "cornuwmrg1"
down_revision = ("cornellphdtui1", "uwtuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
