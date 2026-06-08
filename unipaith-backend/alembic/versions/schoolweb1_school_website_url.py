"""add schools.website_url + MIT/Harvard school websites

Adds the ``website_url`` column to ``schools`` (each academic unit's own official
site, e.g. mitsloan.mit.edu) and re-applies the MIT and Harvard profiles so the
six MIT and twelve Harvard schools link out. Idempotent; no-ops when absent.

Revision ID: schoolweb1
Revises: progclassprof1
"""

import sqlalchemy as sa
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile, mit_profile

revision = "schoolweb1"
down_revision = "progclassprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("schools", sa.Column("website_url", sa.String(length=1000), nullable=True))
    mit_profile.apply(Session(bind=op.get_bind()))
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    op.drop_column("schools", "website_url")
