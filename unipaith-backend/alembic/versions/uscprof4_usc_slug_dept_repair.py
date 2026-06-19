"""USC slug-leak + field-echo department repair (REPAIR_BACKLOG CRITICAL #2)

Re-applies ``usc_profile.apply()`` after the data module was repaired:

- Removes kebab-case catalogue slug prefixes from ``description_text`` (118 rows live)
  and replaces them with verified catalogue prose + a human-readable programme ref.
- Maps field-echo ``department`` values to each program's real USC
  school/college (601 rows were one-off field echoes).
- Enriches astronomy/physics BS catalogue entries so cross-field anti-stub is clean.

Also unifies the two concurrent heads on ``main`` (``chicagodefab1`` +
``purdueheadsmerge1``) into a single head so deploys stay unblocked.

Revision ID: uscprof4
Revises: chicagodefab1, purdueheadsmerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uscprof4"
down_revision = ("chicagodefab1", "purdueheadsmerge1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    usc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == usc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
