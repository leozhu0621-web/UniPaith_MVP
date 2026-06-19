"""Replace Michigan's machine "Catalog entry <hex>:" build-artifact descriptions with
verified, per-credential discipline definitions (REPAIR_BACKLOG run 59, target #1).

Re-applies michigan_profile, which now sources descriptions from the regenerated
michigan_catalogue_descriptions.py (no nonce, no namesake scrape, no division frame;
anti-stub + machine-artifact clean). Idempotent.

Revision ID: michprof4
Revises: uclaprof5
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile

revision = "michprof4"
down_revision = "uclaprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
