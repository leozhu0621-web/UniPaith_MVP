"""University of Florida matcher-core enrichment (REPAIR_BACKLOG #1 / #2 / #4).

Re-applies ``uf_profile.apply()`` after wiring three matcher-core dimensions the
live catalog was missing:
  * #1 ``cip_code`` — a verified 6-digit CIP-2020 code present in ``ref_majors`` on
    every one of the 314 programs (``uf_cip6.CIP6_BY_SLUG``). The base catalog held
    only the 2-digit CIP *family* (e.g. ``45.02``), which never resolves the exact
    ref_majors / field-66 lookup — the same defect the Michigan review fixed, here at
    314/314. Each program is resolved to the specific 6-digit code within its already-
    breadth-verified family (no family drift, no guess).
  * #2 the public-university budget scalar ``program.tuition`` now carries the
    NON-RESIDENT (out-of-state) sticker (the CPEF budget feature reads the flat
    scalar; the cost card + breakdown keep the resident basis and both rates).
  * #4 ``who_its_for`` + ``highlights`` filled on every program from UF published
    audience/fit material (no literal ``= None`` hard-null).

Because ``progprefbf1`` derived program-preference rows while UF ``cip_code`` was
still null, and ``backfill_program_preferences`` only fills EMPTY fields on existing
rows, the corrected CIP would not reach the program -> student field signal. So this
DELETES unclaimed ``source="derived"`` preference rows for UF, then re-derives — the
same recompute the Michigan / brown / emory / purdue / ucla CIP repairs use. Direct
apply (no lock-bounded skip) so the data actually lands; verify-live on content.

Revision ID: ufcipwho1
Revises: michcipwho2
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ufcipwho1"
down_revision = "michcipwho2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uf_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uf_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # Only clear DERIVED rows for UNCLAIMED programs — backfill skips claimed
        # programs, so deleting a claimed row would strand first-party data.
        prog_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if prog_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(prog_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
