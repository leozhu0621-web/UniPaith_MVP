"""Rice campus photo gallery — 5 verified Wikimedia Commons photos

Re-applies ``rice_profile.apply()`` after adding
``school_outcomes.campus_photos`` (a 5-photo verified gallery with per-photo
credits) so the institution detail hero and explore-card header render the
gallery lightbox pattern. Idempotent; no-op when Rice is absent.

Revision ID: riceprof3
Revises: yaleprof4
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile

revision = "riceprof3"
down_revision = "yaleprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    rice_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
