"""Harvard structural de-fabrication — real names, schools, per-credential descriptions.

Re-applies ``harvard_profile.apply()`` after HIGH #4 repair:
  * federal CIP rollup titles resolved to Harvard's real published degrees
    or dropped when an aggregation bucket
  * suffix-diversifier descriptions replaced with per-credential ``_level_body`` prose
  * field-echo departments replaced with real owning Harvard schools
Derives ``program_preferences`` for every Harvard program (skips claimed rows).

Revision ID: harvarddefab1
Revises: penndefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvarddefab1"
down_revision = "penndefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    harvard_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == harvard_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
