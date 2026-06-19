"""Penn structural de-fabrication — real names, schools, per-credential descriptions.

Re-applies ``penn_profile.apply()`` after HIGH #3 repair:
  * federal CIP rollup titles resolved to Penn's real published degrees
    (verified via catalog.upenn.edu) or dropped when an aggregation bucket
  * field-echo departments replaced with the real owning Penn school
  * per-credential description leads (anti-stub clean — 0% verbatim/shared-body)
Derives ``program_preferences`` for every Penn program (skips claimed rows).

Revision ID: penndefab1
Revises: cornellpeer1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "penndefab1"
down_revision = "cornellpeer1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    penn_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == penn_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
