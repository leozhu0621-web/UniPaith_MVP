"""richer MIT campus info (campus_life + campus_basics)

Data-only migration. Re-applies the MIT profile so the About tab's Campus life
section gains student organizations / Greek life / housing and a Campus & basics
location + academic calendar. Idempotent; no-ops when MIT is absent.

Revision ID: campusinfo1
Revises: contentsrc1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "campusinfo1"
down_revision = "contentsrc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
