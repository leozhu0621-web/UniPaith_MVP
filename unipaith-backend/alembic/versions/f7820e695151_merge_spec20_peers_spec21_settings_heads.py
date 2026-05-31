"""Merge the Spec 20 (peers/connect) and Spec 21 (settings) alembic heads.

Spec 21 (``e1f2a3b4c5d6``) and Spec 20 (``e4f5a6b7c8d9``) branched independently
off the Spec 18/17 merge head, leaving two heads. This no-op merge resolves
``alembic upgrade head`` to a single head.

Revision ID: f7820e695151
Revises: e1f2a3b4c5d6, e4f5a6b7c8d9
Create Date: 2026-05-31

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "f7820e695151"  # pragma: allowlist secret
down_revision = ("e1f2a3b4c5d6", "e4f5a6b7c8d9")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
