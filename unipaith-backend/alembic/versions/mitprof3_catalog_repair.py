"""MIT catalog repair — departments, disambiguated names, campus gallery

Re-applies ``unipaith.data.mit_profile.apply()`` so every program carries a
real ``department``, credential-disambiguated ``program_name`` (no duplicate bare
field titles or bare "MBA"), a verified 5-photo ``campus_photos`` gallery, and
``ENRICHED_AT`` / ``_standard`` stamps at the current STANDARD_VERSION.

Revision ID: mitprof3
Revises: caltechprof5
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitprof3"
down_revision = "caltechprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    mit_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
