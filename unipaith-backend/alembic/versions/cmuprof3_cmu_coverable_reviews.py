"""Carnegie Mellon profile repair — coverable external_reviews depth pass

Re-applies ``unipaith.data.carnegie_mellon_profile.apply()`` so 26 additional
coverable programs (SCS, Robotics Institute, ECE/INI, Heinz, Tepper, College of
Fine Arts, and flagship undergraduate majors) gain aggregated, cited
``external_reviews`` in the MBAn shape. Idempotent: ``apply()`` upserts by slug
and is a no-op when CMU is absent (fresh/CI databases).

Revision ID: cmuprof3
Revises: cornellprof3
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof3"
down_revision = "cornellprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    carnegie_mellon_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
