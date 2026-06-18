"""Repair UW profile to gold: news RSS on all nodes, credential-disambiguated
program names, field-specific descriptions, and coverable external_reviews.

Revision ID: uwaprof2
Revises: uclaprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile

revision = "uwaprof2"
down_revision = "uclaprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
