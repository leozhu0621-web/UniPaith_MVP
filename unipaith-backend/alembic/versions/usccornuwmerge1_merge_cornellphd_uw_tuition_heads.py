"""Merge dual head cornellphdtui1 + uwtuition1 (auto-merge race on cmutuition1).

Both revisions branched from ``cmutuition1`` (#1073 CMU tuition + #1071 Cornell PhD tuition
follow-up + #1074 UW tuition). Unifies to a single head before the USC tuition backfill.

Revision ID: usccornuwmerge1
Revises: cornellphdtui1, uwtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

revision = "usccornuwmerge1"
down_revision = ("cornellphdtui1", "uwtuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
