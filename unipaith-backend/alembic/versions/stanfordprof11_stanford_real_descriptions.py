"""Replace Stanford's machine "Catalog entry <hex>:" build-artifact descriptions with
verified, per-credential discipline definitions (REPAIR_BACKLOG run 59, Stanford target).

Re-applies stanford_profile, which now sources descriptions from the regenerated
stanford_catalogue_descriptions.py (no nonce, no division frame; anti-stub +
machine-artifact clean). Idempotent.

Revision ID: stanfordprof11
Revises: michprof4
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof11"
down_revision = "michprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
