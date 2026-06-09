"""school about_detail (richer About tab + faculty)

Adds schools.about_detail JSONB and re-applies the MIT profile so the Sloan
School row gains its expanded description + sourced founded/named-for/leadership/
faculty/research-centers detail. Idempotent; no-ops when MIT is absent.

Revision ID: schooldetail1
Revises: imgurl1
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "schooldetail1"
down_revision = "imgurl1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("schools", sa.Column("about_detail", JSONB, nullable=True))
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    op.drop_column("schools", "about_detail")
