"""Cornell structural de-fabrication — real names, departments, per-credential descriptions.

Re-applies ``cornell_profile.apply()`` after HIGH #5 repair:
  * federal CIP rollup titles resolved to Cornell's real published degrees
    (verified via courses.cornell.edu) or dropped when an aggregation bucket
  * field-echo departments replaced with the real owning Cornell college
  * per-credential description leads (anti-stub clean — 0% verbatim/shared-body)
Derives ``program_preferences`` for every Cornell program (skips claimed rows).

Revision ID: cornelldefab1
Revises: buberkmerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornelldefab1"
down_revision = "buberkmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == cornell_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
