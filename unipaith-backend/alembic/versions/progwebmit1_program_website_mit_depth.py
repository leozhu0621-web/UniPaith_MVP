"""add programs.website_url + MIT full names / URLs / in-depth About / detailed admissions

Adds the ``website_url`` column to ``programs`` (the school's own official page
for a program), then re-applies the canonical MIT profile so every MIT program
gets its full official degree name as the title, a verified official
program-page URL, fuller in-depth descriptions for flagship programs, and richer
application requirements (deadline rounds, application fee, test ranges,
evaluation notes). Idempotent data re-apply; no-ops when MIT is absent.

Revision ID: progwebmit1
Revises: harvardprof2
"""

import sqlalchemy as sa
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "progwebmit1"
down_revision = "harvardprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("programs", sa.Column("website_url", sa.String(length=1000), nullable=True))
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    op.drop_column("programs", "website_url")
