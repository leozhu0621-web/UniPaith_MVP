"""New York University — gold-standard profile repair (feeds, descriptions, reviews).

Idempotent data migration: calls ``nyu_profile.apply()`` which upserts verified
``news_rss`` content_sources on every node, field-specific program descriptions,
disambiguated duplicate program names, and external reviews for all coverable programs.

Revision ID: nyuprof2
Revises: uscprof2
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile

revision = "nyuprof2"
down_revision = "uscprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    nyu_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
