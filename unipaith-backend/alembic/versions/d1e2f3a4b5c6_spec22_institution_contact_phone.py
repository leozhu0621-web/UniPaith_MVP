"""Spec 22 §3 — institution contact phone on public profile.

Revision ID: d1e2f3a4b5c6
Revises: a8263041209b
Create Date: 2026-06-01
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "d1e2f3a4b5c6"  # pragma: allowlist secret
down_revision = "a8263041209b"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("institutions", sa.Column("contact_phone", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("institutions", "contact_phone")
