"""UCSD credential descriptions — per-level bodies + fabricated-unit fix

Re-applies ``ucsd_profile.apply()`` after replacing shared field-level descriptions
with distinct per-credential bodies and removing the fabricated aerospace center.
Idempotent; no-op when absent.

Revision ID: ucsdprof7
Revises: ucsdprof6
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile

revision = "ucsdprof7"
down_revision = "ucsdprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ucsd_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
