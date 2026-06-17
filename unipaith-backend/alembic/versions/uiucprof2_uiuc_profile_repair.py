"""Repair UIUC profile to gold: news RSS on all nodes, credential-disambiguated
program names, field-specific descriptions, and coverable external_reviews.

Revision ID: uiucprof2
Revises: nyuprof2
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile

revision = "uiucprof2"
down_revision = "nyuprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uiuc_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
