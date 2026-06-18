"""Repair UCLA: replace the build-artifact-assembly descriptions (per-row
"Catalog entry <hex>:" nonce + school-division frame + scraped-namesake text,
REPAIR_BACKLOG run 59 critical #1) with real, verified per-program prose for all
373 programs — UCLA General Catalog 2025 + de-namesaked Wikipedia discipline
summaries + hand-verified UCLA prose. Idempotent re-apply (replace=True).

Revision ID: uclaprof4
Revises: uwseedmerge1
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile

revision = "uclaprof4"
down_revision = "uwseedmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
