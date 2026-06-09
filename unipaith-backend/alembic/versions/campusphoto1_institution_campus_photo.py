"""lead institution media_gallery with a real campus photo

Data-only migration. Re-applies the MIT and Harvard profiles so each
institution's media_gallery leads with a real (raster) campus photo, which the
detail-page hero renders. The gallery previously held only the logo SVG, so the
hero fell back to a blank gradient. Idempotent; no-ops when absent.

Revision ID: campusphoto1
Revises: mbancost1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile, mit_profile

revision = "campusphoto1"
down_revision = "mbancost1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
