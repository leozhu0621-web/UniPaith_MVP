"""UChicago profile repair — content_sources on every node + full IPEDS catalog

Populates University of Chicago institution/school/program ``content_sources``
(UChicago News Feedburner RSS + campus events iCal + keyword filters), expands the
program catalog to the IPEDS completions-cip-6 list (UNITID 144050), and refreshes
conformance stamps — via ``chicago_profile.apply()``.

Revision ID: chicagoprof2
Revises: pennprof4
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile

revision = "chicagoprof2"
down_revision = "pennprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    chicago_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
