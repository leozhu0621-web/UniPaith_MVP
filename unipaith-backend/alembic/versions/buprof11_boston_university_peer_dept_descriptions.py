"""Boston University — remove Medill peer signature, fix field-echo departments, anti-stub clean.

Re-applies ``bu_profile.apply()`` after CRITICAL #1 repair:
  * Northwestern Medill peer signature removed from COM public-relations rows
  * field-echo ``department`` values mapped to real owning schools/colleges (0% echo)
  * per-credential ``FIELD_DEGREE_DESCRIPTIONS`` for shared-leading-body fields
  * slug-specific descriptions for cross-school credential siblings
Derives ``program_preferences`` for every BU program (skips claimed rows).

Revision ID: buprof11
Revises: uiucslugfix1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "buprof11"
down_revision = "uiucslugfix1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
