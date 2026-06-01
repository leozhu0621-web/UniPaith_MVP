"""Merge the Spec 35 (enrollment yield) and Spec 36 (audit log) heads.

Both ``t35a1b2c3d4e`` and ``a36auditlog1b2c`` branch off ``d33a1b2c4e5f``; they
landed concurrently. This is a pure merge point (no schema change) so the graph
keeps a single head (``test_alembic_has_single_head`` gates the backend deploy).

Revision ID: s3536merge1a2b
Revises: a36auditlog1b2c, t35a1b2c3d4e
Create Date: 2026-06-01

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "s3536merge1a2b"  # pragma: allowlist secret
down_revision = ("a36auditlog1b2c", "t35a1b2c3d4e")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
