"""Columbia structural de-fabrication — real names, schools, per-credential descriptions.

Re-applies ``columbia_profile.apply()`` after REPAIR_BACKLOG HIGH #1 repair:
  * federal CIP rollup titles resolved to Columbia's real published degrees
    or dropped when an aggregation bucket
  * possessive IPEDS award-level names replaced with conferred designations
  * field-echo departments replaced with real owning Columbia schools
  * suffix-diversifier descriptions replaced with per-credential ``_level_body`` prose
Derives ``program_preferences`` for every Columbia program (skips claimed rows).

Revision ID: columbiadefab1
Revises: harvarddefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "columbiadefab1"
down_revision = "harvarddefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    columbia_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == columbia_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
