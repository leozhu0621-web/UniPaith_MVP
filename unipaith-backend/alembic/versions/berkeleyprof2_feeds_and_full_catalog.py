"""Berkeley profile repair — content_sources on every node + full Scorecard catalog

Populates UC Berkeley's institution/school/program ``content_sources`` (Berkeley News
RSS + academic-calendar iCal + keyword filters), expands the program catalog to the
College Scorecard Field-of-Study list (UNITID 110635), adds graduate/professional
schools, media credit, and conformance stamps — via ``berkeley_profile.apply()``.

Revision ID: berkeleyprof2
Revises: cornellfeeds1
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof2"
down_revision = "cornellfeeds1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    berkeley_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
