"""Merge the dual migration heads from concurrent auto-merges.

``purduedefab1`` (Purdue description de-fabrication, #832) and ``schol1a2b3c4d``
(external_scholarships table, #828) both branched off ``progprefbf1`` and auto-merged,
leaving ``main`` with two heads — which fails ``test_alembic_has_single_head`` and
blocks every backend deploy. This is an empty merge: no schema or data change, it only
unifies the heads.

Revision ID: purduescholmerge1
Revises: purduedefab1, schol1a2b3c4d
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "purduescholmerge1"
down_revision = ("purduedefab1", "schol1a2b3c4d")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
