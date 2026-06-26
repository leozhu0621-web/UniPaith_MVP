"""Michigan matcher-core enrichment (REPAIR_BACKLOG #1 / #2 / #4).

Re-applies ``michigan_profile.apply()`` after wiring three matcher-core dimensions
the live catalog was missing:
  * #1 ``cip_code`` — a standard IPEDS CIP-2020 code on every one of the 379 programs
    (the CIP join key to ``ref_majors`` + the field-66 interest/field signal).
  * #2 the public-university budget scalar ``program.tuition`` now carries the
    NON-RESIDENT (out-of-state) sticker (the CPEF budget feature reads the flat
    scalar; the cost card + breakdown keep the resident basis and both rates).
  * #4 ``who_its_for`` + ``highlights`` filled on every program (the literal
    ``p.<field> = None`` hard-nulls were removed).

Re-derives program-preference rows so the program -> student match direction stays
covered. Direct apply (no lock-bounded skip) so the data actually lands; verify-live
on content after deploy.

Revision ID: michcipwho1
Revises: browncipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "michcipwho1"
down_revision = "browncipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == michigan_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
