"""add programs.class_profile + MIT MBAn gold-standard program detail

Adds the ``class_profile`` JSONB column to ``programs`` (cohort size,
selectivity, composition) and re-applies the canonical MIT profile so the
reference program — MIT Sloan's Master of Business Analytics (MBAn) — carries
program-specific (sourced) cost, outcomes, admissions, curriculum, highlights,
in-depth description, and class profile. Idempotent; no-ops when MIT is absent.

Revision ID: progclassprof1
Revises: progwebharv1
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "progclassprof1"
down_revision = "progwebharv1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("programs", sa.Column("class_profile", JSONB, nullable=True))
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    op.drop_column("programs", "class_profile")
