"""MBAn outcomes refreshed to the verified Class of 2025 employment report

Data-only migration. Re-applies the MIT profile so the MBAn program's
outcomes_data carries the verified Class of 2025 figures (median base $143K,
25th/75th $120K/$155K, 98.5% employed within 6 months, real top industries
incl. Consulting, top employers, and the CSEA methodology conditions) plus a
canonical source URL. Replaces the earlier 2024 figures and the fabricated
salary range. Idempotent; no-ops when MIT is absent.

Revision ID: mbanoutcomes1
Revises: campusres1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mbanoutcomes1"
down_revision = "campusres1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
