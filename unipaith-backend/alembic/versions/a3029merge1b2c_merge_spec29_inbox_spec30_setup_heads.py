"""Merge the concurrent institution heads (Spec 28 / 29 / 30).

Spec 28 (``a28b1c2d3e4f`` attribution), Spec 29 (``g29a1b2c3d4e`` inbox) and
Spec 30 (``f30a1b2c3d45`` setup) each branched off ``f27e5a1c0d34`` in concurrent
PRs, leaving three alembic heads. This empty merge revision rejoins them into a
single linear head (``test_alembic_has_single_head``). No schema change.

Revision ID: a3029merge1b2c
Revises: f30a1b2c3d45, g29a1b2c3d4e, a28b1c2d3e4f
Create Date: 2026-06-01

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "a3029merge1b2c"  # pragma: allowlist secret
down_revision = ("f30a1b2c3d45", "g29a1b2c3d4e", "a28b1c2d3e4f")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
