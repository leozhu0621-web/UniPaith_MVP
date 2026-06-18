"""NYU — bulletin-sourced descriptions, real departments, remove synthesized reviews.

Re-applies ``nyu_profile.apply()`` after replacing school-blurb fabrication with
507 verified NYU Bulletin Program Description texts, setting ``department`` to the
real owning school/college, and dropping 152 synthesized institution-level reviews
(honest omit for coverable programs pending gathered coverage).

Revision ID: nyuprof3
Revises: ucsdprof8
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile

revision = "nyuprof3"
down_revision = "ucsdprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    nyu_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
