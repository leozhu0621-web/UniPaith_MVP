"""Boston University catalog structural repair + working news feed

De-fabricates the BU catalog: collapses concentration-split padding rows into
tracks, replaces 96% template-description stubs with field-specific descriptions,
fixes title-cased/CIP department tokens, repairs degree-name mismatches, and
points content_sources at the verified BUniverse RSS + university calendar iCal
(BU Today WordPress RSS is empty). Re-applies ``bu_profile.apply()``.

Revision ID: buprof8
Revises: princetonprof6
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof8"
down_revision = "princetonprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
