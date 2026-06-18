"""De-fabricate JHU catalog: per-credential field-specific descriptions so a field's
credential siblings (BS / MS / certificate / PhD) no longer share one verbatim clause
(run-58 verbatim-across-levels defect). Names, real departments, and the 45 genuine
program-specific external_reviews are unchanged.

Revision ID: jhudefab1
Revises: uwprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhudefab1"
down_revision = "uwprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    jhu_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
