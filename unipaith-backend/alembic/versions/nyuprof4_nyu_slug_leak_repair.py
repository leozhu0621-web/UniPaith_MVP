"""NYU slug-leak description repair (REPAIR_BACKLOG CRITICAL #2)

Re-applies ``nyu_profile.apply()`` after the data module was repaired:

- Removes kebab-case bulletin slug prefixes from ``description_text`` (41 rows live)
  and replaces them with verified bulletin prose + a human-readable programme ref.

Revision ID: nyuprof4
Revises: uscprof4
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyuprof4"
down_revision = "uscprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
