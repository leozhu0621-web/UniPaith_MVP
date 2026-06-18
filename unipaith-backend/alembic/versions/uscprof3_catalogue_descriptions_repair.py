"""Repair USC profile: catalogue-sourced program descriptions (anti-stub clean).

Replaces school-blurb field clauses and synthesized review padding with verified
first-party prose from catalogue.usc.edu for all 613 programs. Drops
``usc_field_descriptions`` / ``usc_reviews_generated`` stubs from the apply path.

Idempotent via ``unipaith.data.usc_profile.apply()``.

Revision ID: uscprof3
Revises: princetonprof10
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile

revision = "uscprof3"
down_revision = "princetonprof10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    usc_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
