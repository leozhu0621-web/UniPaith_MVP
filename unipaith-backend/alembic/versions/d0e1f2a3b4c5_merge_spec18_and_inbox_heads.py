"""Merge Spec 18 (offers/decisions) and Spec 17 (inbox) alembic heads.

Spec 18 (``c8d2e1a3f5b6``) and the Spec 17 inbox head (``c5d6e7f8a9b0``)
branched independently off the Spec 16 calendar head, leaving two heads.
This is a no-op merge so ``alembic upgrade head`` resolves to a single head.

Revision ID: d0e1f2a3b4c5
Revises: c5d6e7f8a9b0, c8d2e1a3f5b6
Create Date: 2026-05-31

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "d0e1f2a3b4c5"  # pragma: allowlist secret
down_revision = ("c5d6e7f8a9b0", "c8d2e1a3f5b6")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
