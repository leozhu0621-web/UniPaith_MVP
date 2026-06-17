"""Caltech field-specific program descriptions — full catalog de-stub

Re-applies ``caltech_profile.apply()`` after replacing all classification-only
program descriptions with verified field-specific clauses (90/90 programs; 0%
classification stubs; 0% name-prefix descriptions). Idempotent; no-op when absent.

Revision ID: caltechprof7
Revises: uwprof1
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile

revision = "caltechprof7"
down_revision = "uwprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    caltech_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
