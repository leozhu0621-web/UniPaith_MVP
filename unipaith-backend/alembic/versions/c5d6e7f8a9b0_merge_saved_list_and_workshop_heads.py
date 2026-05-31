"""Merge Spec 13 saved-list and workshop-runs alembic heads.

Revision ID: c5d6e7f8a9b0
Revises: b3c4d5e6f7a8, f7a8b9c0d1e2
Create Date: 2026-05-31 19:45:00.000000

"""

revision = "c5d6e7f8a9b0"  # pragma: allowlist secret
down_revision = ("b3c4d5e6f7a8", "f7a8b9c0d1e2")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
