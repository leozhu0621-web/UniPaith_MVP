"""Repair Michigan profile to gold: news RSS on all nodes, credential-disambiguated
program names, field-specific descriptions, and coverable external_reviews.

Revision ID: michprof2
Revises: uiucprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile

revision = "michprof2"
down_revision = "uiucprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
