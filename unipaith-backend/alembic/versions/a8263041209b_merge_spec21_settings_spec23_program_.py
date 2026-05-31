"""Merge the Spec 21 (settings) and Spec 23 (program editor) alembic heads.

Spec 21's merge head (``f7820e695151``) and Spec 23's program-editor migration
(``e7a1c4d9b230``) landed on main independently, leaving two heads. This no-op
merge resolves ``alembic upgrade head`` to a single head.

Revision ID: a8263041209b
Revises: f7820e695151, e7a1c4d9b230
Create Date: 2026-05-31

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "a8263041209b"  # pragma: allowlist secret
down_revision = ("f7820e695151", "e7a1c4d9b230")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
