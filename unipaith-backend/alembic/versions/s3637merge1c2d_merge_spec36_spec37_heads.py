"""Merge the Spec 35+36 head and the Spec 37 (AI extensibility) head.

``s3536merge1a2b`` (the enrollment-yield + audit-log merge) and
``e37a1b2c3d4f`` (Spec 37 ai_config) both descend from ``t35a1b2c3d4e`` and
landed concurrently, leaving two heads. This is a pure merge point (no schema
change) so the graph keeps a single head (``test_alembic_has_single_head`` gates
the backend deploy).

Revision ID: s3637merge1c2d
Revises: s3536merge1a2b, e37a1b2c3d4f
Create Date: 2026-06-01

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "s3637merge1c2d"  # pragma: allowlist secret
down_revision = ("s3536merge1a2b", "e37a1b2c3d4f")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
