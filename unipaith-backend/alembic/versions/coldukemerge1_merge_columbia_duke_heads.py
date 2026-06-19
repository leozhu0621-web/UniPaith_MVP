"""merge columbia (columbiadefab2) + duke (dukedefab1) de-fabrication heads

Auto-merge race: PR #866 (columbiadefab2) and #868 (dukedefab1) both branched off
``colyalemerge1`` and merged to main, leaving two alembic heads. This merge-only
migration unifies them so ``test_alembic_has_single_head`` passes and Deploy Backend
is unblocked. No schema/data changes (both parents already applied their data).

Revision ID: coldukemerge1
Revises: columbiadefab2, dukedefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "coldukemerge1"
down_revision = ("columbiadefab2", "dukedefab1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
