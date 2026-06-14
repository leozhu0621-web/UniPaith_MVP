"""Princeton campus photo gallery — 5 verified Wikimedia Commons photos

Re-applies ``princeton_profile.apply()`` after adding ``school_outcomes.campus_photos``
(a 5-photo verified gallery with per-photo credits) so the institution detail hero
and explore-card header render the gallery lightbox pattern. Idempotent; no-op when
Princeton is absent.

Revision ID: princetonprof5
Revises: mitprof3
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof5"
down_revision = "mitprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    princeton_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
