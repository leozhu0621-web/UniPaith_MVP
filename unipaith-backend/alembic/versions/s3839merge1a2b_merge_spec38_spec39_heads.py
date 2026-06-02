"""Merge the Spec 38 (international admissions) head and the Spec 39 (fees &
payments) head.

``i38a1b2c3d4e`` (Spec 38) and ``s39a1b2c3d4e`` (Spec 39) both descend from
``s3637merge1c2d`` and landed concurrently, leaving two heads. This is a pure
merge point (no schema change) so the graph keeps a single head
(``test_alembic_has_single_head`` gates the backend deploy).

Revision ID: s3839merge1a2b
Revises: i38a1b2c3d4e, s39a1b2c3d4e
Create Date: 2026-06-01

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "s3839merge1a2b"  # pragma: allowlist secret
down_revision = ("i38a1b2c3d4e", "s39a1b2c3d4e")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
