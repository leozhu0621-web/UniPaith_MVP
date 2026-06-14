"""Carnegie Mellon campus photo gallery — 5 verified Wikimedia Commons photos

Re-applies ``carnegie_mellon_profile.apply()`` after adding
``school_outcomes.campus_photos`` (a 5-photo verified gallery with per-photo
credits) so the institution detail hero and explore-card header render the
gallery lightbox pattern. Idempotent; no-op when CMU is absent.

Revision ID: cmuprof3
Revises: princetonprof5
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof3"
down_revision = "princetonprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    carnegie_mellon_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
