"""Berkeley structural de-fabrication — real names, departments, per-credential descriptions.

Re-applies ``berkeley_profile.apply()`` after HIGH #4 repair:
  * federal CIP rollup titles mapped to Berkeley's real published departments
  * ``Bachelor's in {rollup}`` credential-prefix names replaced with real B.A./B.S./M.S./Ph.D.
  * IPEDS padding rows with no distinct Berkeley degree dropped
  * per-credential descriptions (anti-stub clean — 0% verbatim/shared-body)
Derives ``program_preferences`` for every Berkeley program (skips claimed rows).

Revision ID: berkeleyprof9
Revises: buprof11
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleyprof9"
down_revision = "budefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    berkeley_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == berkeley_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
