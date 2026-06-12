"""Rice University profile repair — media_credit, Full-Time MBA depth, coverable reviews.

Adds campus-photo attribution, deepens the Rice Business Full-Time MBA (outcomes, tracks,
class profile), and fills external_reviews for six coverable programs. Idempotent; no-ops
when Rice is absent.

Revision ID: riceprof2
Revises: dukeprof2
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile

revision = "riceprof2"
down_revision = "dukeprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    rice_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
