"""De-fabricate UW program descriptions: replace the machine-corrupted catalogue
text (which opened "Catalog entry <hex>: Catalog entry <hex>: …", said "Westwood
campus" — UCLA's neighborhood, not Seattle — and used mismatched-article leads such
as "American Music Awards") with verified, per-credential, field-specific
descriptions sourced from the English Wikipedia lead for each discipline, on the
correct Seattle campus. Re-applies uw_profile.apply (idempotent, by slug).

Revision ID: uwdefab1
Revises: uwprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile

revision = "uwdefab1"
down_revision = "jhudefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
