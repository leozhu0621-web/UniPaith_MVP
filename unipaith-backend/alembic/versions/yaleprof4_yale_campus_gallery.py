"""Yale campus photo gallery — 5 verified Wikimedia Commons photos

Re-applies ``yale_profile.apply()`` after adding
``school_outcomes.campus_photos`` (a 5-photo verified gallery with per-photo
credits) so the institution detail hero and explore-card header render the
gallery lightbox pattern. Idempotent; no-op when Yale is absent.

Revision ID: yaleprof4
Revises: columbiaprof7
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile

revision = "yaleprof4"
down_revision = "columbiaprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    yale_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
