"""Penn profile repair — coverable external_reviews on fourteen programs.

Re-applies ``unipaith.data.penn_profile.apply()`` so the Wharton MBA, Perelman MD,
Penn Carey Law JD, six resume graduate/professional school flagships, and five key
undergraduate options carry aggregated, cited external_reviews in the MBAn shape.

Revision ID: pennprof5
Revises: caltechprof4
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof5"
down_revision = "caltechprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    penn_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
