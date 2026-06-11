"""Princeton profile repair — content_sources on every node + full IPEDS catalog

Populates Princeton University institution/school/program ``content_sources``
(Princeton News RSS + public events RSS + keyword filters), expands the program
catalog to the College Scorecard Field-of-Study list (UNITID 186131), adds campus
photo ``media_credit``, and refreshes conformance stamps — via
``princeton_profile.apply()``.

Revision ID: princetonprof2
Revises: chicagoprof2
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof2"
down_revision = "chicagoprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    princeton_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
