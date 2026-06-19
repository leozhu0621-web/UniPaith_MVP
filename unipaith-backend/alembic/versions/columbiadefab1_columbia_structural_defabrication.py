"""Columbia structural de-fabrication — real degree catalog, real departments, clean descriptions.

Re-applies ``columbia_profile.apply()`` after HIGH #1 repair (columbiadefab1):
  * the IPEDS×award-level catalog (263 rows: possessive "Bachelor's in {CIP rollup}"
    names, field-echo departments, 88 fabricated departmental "graduate certificates")
    is replaced by Columbia's REAL degree set — 167 programs with conferred designations,
    real owning departments, and per-credential field-specific descriptions
  * descriptions that imported PEER-institution units (Harvard's Nieman Foundation,
    Carpenter Center, and Visual & Environmental Studies program) are removed
  * two real schools added: the Graduate School of Arts and Sciences (it confers the
    arts-&-sciences PhD/MA the prior catalog mis-assigned to Columbia College) and the
    College of Dental Medicine (D.D.S.)
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
