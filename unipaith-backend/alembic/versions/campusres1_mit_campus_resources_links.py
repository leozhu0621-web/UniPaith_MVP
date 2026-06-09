"""MIT campus resources links (lab homepages + student-resource hubs)

Data-only migration. Re-applies the MIT profile so school_outcomes gains
research.lab_links (official lab/institute homepages) and campus_life.resources
(athletics / arts / housing / student-life hubs) for the merged "Campus
resources" card. Idempotent; no-ops when MIT is absent.

Revision ID: campusres1
Revises: schooldetail1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "campusres1"
down_revision = "schooldetail1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
