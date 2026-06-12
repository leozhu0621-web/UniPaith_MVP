"""Stanford profile repair — coverable external_reviews on 13 programs

Adds aggregated external_reviews on the GSB MBA/MSx, CS MS/BS, JD, MD, MS&E,
EE MS, and key undergraduate options (ME, economics, symbolic systems, human
biology, bioengineering), and refreshes conformance stamps via
``stanford_profile.apply()``.

Revision ID: stanfordprof3
Revises: princetonprof3
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof3"
down_revision = "princetonprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
