"""De-fabricate UCLA program descriptions: replace machine-corrupted catalogue
text (which opened "Catalog entry <hex>: …" and used namesake Wikipedia scrapes)
with verified, per-credential, field-specific descriptions sourced from the
English Wikipedia lead for each discipline, on the correct Westwood campus.
Re-applies ucla_profile.apply (idempotent, by slug).

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
