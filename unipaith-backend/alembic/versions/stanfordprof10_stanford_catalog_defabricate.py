"""De-fabricate Stanford program catalog (REPAIR_BACKLOG critical #2).

Replaces CIP-rollup program names, field-echo departments, and per-field stub
descriptions with verified catalogue names, real owning departments, and per-slug
descriptions; removes 28 synthesized external_reviews (DEPTH_REVIEWS). Idempotent.

Revision ID: stanfordprof10
Revises: uwprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof10"
down_revision = "uwprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
