"""Cornell per-credential descriptions + peer-signature gate + Area Studies drop.

Re-applies ``cornell_profile.apply()`` after cornelldecontam1 (CRITICAL #1 follow-up):
  * replace shared _LEVEL_LEAD stubs with per-credential researched bodies
    (gold MIT model — 0% shared leading body across credential siblings)
  * build-time ``_PEER_SIGNATURES`` gate prevents cross-institution unit regression
  * drop federal Area Studies rollup rows (no single named Cornell degree)
Derives ``program_preferences`` for every Cornell program (skips claimed rows).

Revision ID: cornellpeer1
Revises: cornelldecontam1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellpeer1"
down_revision = "cornelldecontam1"
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
