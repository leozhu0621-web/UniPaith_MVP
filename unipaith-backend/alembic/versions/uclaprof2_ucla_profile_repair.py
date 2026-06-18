"""Repair UCLA profile to gold: news RSS on all nodes, credential-disambiguated
program names, field-specific descriptions, and coverable external_reviews.

Revision ID: uclaprof2
Revises: michprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile

revision = "uclaprof2"
down_revision = "michprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
