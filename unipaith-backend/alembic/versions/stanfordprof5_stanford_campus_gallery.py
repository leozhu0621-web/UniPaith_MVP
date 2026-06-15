"""Stanford campus photo gallery — 5 verified Wikimedia Commons photos

Re-applies ``stanford_profile.apply()`` after adding
``school_outcomes.campus_photos`` (a 5-photo verified gallery with per-photo
credits) so the institution detail hero and explore-card header render the
gallery lightbox pattern. Idempotent; no-op when Stanford is absent.

Revision ID: stanfordprof5
Revises: riceprof3
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof5"
down_revision = "riceprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    stanford_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
