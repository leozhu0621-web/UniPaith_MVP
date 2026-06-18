"""Repair UT Austin profile to gold: news RSS on all nodes, credential-disambiguated
program names, field-specific descriptions, and coverable external_reviews.

Revision ID: utaprof1
Revises: uwaprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile

revision = "utaprof1"
down_revision = "uwaprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
