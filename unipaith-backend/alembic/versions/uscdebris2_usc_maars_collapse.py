"""USC MAARS concentration collapse + residual garbled-name fix (follow-up to uscdebris1)

uscdebris1 fixed one of the two Master of Advanced Architectural Research Studies (MAARS)
concentration rows; the second (Performative Design and Technology) still shipped a garbled
cross-field name minted from a wrong ``_CODE_PREFIX`` ("Master of Arts in Art and Curatorial
Practices in Advanced Architectural Research Studies"). Both MAARS concentrations are now
collapsed into one base degree ("Master of Advanced Architectural Research Studies") carrying
the concentrations as ``tracks``.

Re-applies ``usc_profile.apply()`` (idempotent: upserts by slug, deletes non-canonical rows,
so the two old MAARS slugs are removed and the single survivor remains) + the
``program_preferences`` backfill.

Revision ID: uscdebris2
Revises: bupercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uscdebris2"
down_revision = "bupercred1"
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
