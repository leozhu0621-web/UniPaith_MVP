"""University of Florida matcher-core enrichment (REPAIR_BACKLOG #1 / #2 / #4).

Re-applies ``uf_profile.apply()`` after wiring three matcher-core dimensions the
live catalog was missing:
  * #1 ``cip_code`` — the IPEDS CIP-2020 code (already used for the breadth
    cross-check) is now stamped on every one of the 314 programs (the CIP join
    key to ``ref_majors`` + the field-66 interest/field signal).
  * #2 the public-university budget scalar ``program.tuition`` now carries the
    NON-RESIDENT (out-of-state) sticker (the CPEF budget feature reads the flat
    scalar; the cost card + breakdown keep the resident basis and both rates).
  * #4 ``who_its_for`` + ``highlights`` filled on every program from UF's
    published audience/fit material (no literal ``= None`` hard-null).

Re-derives program-preference rows so the program -> student match direction stays
covered. Direct apply (no lock-bounded skip) so the data actually lands; verify-live
on content after deploy.

Revision ID: ufcipwho1
Revises: michcipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ufcipwho1"
down_revision = "michcipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uf_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uf_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
