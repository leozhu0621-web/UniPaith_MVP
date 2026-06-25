"""Berkeley — resolve the federal CIP-rollup "Area Studies"/"Liberal Arts and Sciences" names.

Re-applies ``berkeley_profile.apply()`` after the REPAIR_BACKLOG #1 fix:
  * CIP 05.01 "Area Studies" → real degrees: B.A. American Studies + M.A. Asian Studies
    (Group in Asian Studies); the federal-bucket Ph.D. row (no standalone area-studies
    doctorate at Berkeley — designated emphases only) is dropped.
  * CIP 24.01 "Liberal Arts and Sciences, General Studies and Humanities" → real
    B.A. Interdisciplinary Studies (the ISF major).
  * CIP 30.20 row renamed from "Global Studies Program" to the real "Global Studies"
    major (clears the department==field echo).
``apply()`` is idempotent and reconciles the dropped Ph.D. slug (delete-if-unreferenced,
else unpublish). Derives ``program_preferences`` for every Berkeley program (skips claimed).

Revision ID: berkeleyareastudies1
Revises: brownprof1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleyareastudies1"
down_revision = "brownprof1"
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
