"""UChicago catalog repair — departments, disambiguated names, campus gallery

Re-applies ``unipaith.data.chicago_profile.apply()`` so every program carries a
real ``department``, credential-disambiguated ``program_name`` (no duplicate bare
field titles), a verified 5-photo ``campus_photos`` gallery, and
``ENRICHED_AT`` / ``_standard`` stamps at the current STANDARD_VERSION.

Revision ID: chicagoprof4
Revises: dukeprof3
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile

revision = "chicagoprof4"
down_revision = "dukeprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    chicago_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
