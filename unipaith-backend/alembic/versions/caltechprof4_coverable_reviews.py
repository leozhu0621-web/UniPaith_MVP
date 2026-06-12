"""Caltech profile repair — coverable external_reviews on fifteen programs.

Re-applies ``unipaith.data.caltech_profile.apply()`` so the flagship CS option plus
fourteen other coverable undergraduate options and MS degrees carry aggregated,
cited external_reviews in the MBAn shape.

Revision ID: caltechprof4
Revises: chicagoprof3
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile

revision = "caltechprof4"
down_revision = "chicagoprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    caltech_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
