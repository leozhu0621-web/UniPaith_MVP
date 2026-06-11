"""Penn profile repair — content_sources on every node + full IPEDS catalog

Populates University of Pennsylvania institution/school/program ``content_sources``
(Penn Today RSS + Almanac academic-calendar iCal + keyword filters), expands the
program catalog to the IPEDS completions-cip-6 list (UNITID 215062), adds campus photo
``media_credit``, and conformance stamps — via ``penn_profile.apply()``.

Revision ID: pennprof4
Revises: berkeleyprof2
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof4"
down_revision = "berkeleyprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    penn_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
