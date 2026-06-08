"""add programs.external_reviews + MBAn faculty & cited reviews

Adds the ``external_reviews`` JSONB column to ``programs`` and re-applies the MIT
profile so the reference program (MIT Sloan MBAn) carries its faculty lead +
directory link (in faculty_contacts) and aggregated, cited student-review themes
from public third-party sources (external_reviews). Idempotent; no-ops when MIT
is absent.

Revision ID: progreviews1
Revises: schoolweb1
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "progreviews1"
down_revision = "schoolweb1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("programs", sa.Column("external_reviews", JSONB, nullable=True))
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    op.drop_column("programs", "external_reviews")
