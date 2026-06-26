"""Northwestern matcher-core enrichment (REPAIR_BACKLOG #1 / #4).

Re-applies ``northwestern_profile.apply()`` after wiring two matcher-core dimensions the
live catalog (125 programs) was missing:
  * #1 ``cip_code`` — the verified IPEDS / College Scorecard CIP-2020 family code already
    carried on every program spec (used for the catalog breadth cross-check) is now stamped
    onto ``Program.cip_code``. The base ``apply()`` never assigned it, so the matcher scored
    every Northwestern program field-blind; the CPEF field signal resolves on the CIP 2-digit
    family + program-name aliases (``services/match/field_canon.fields_offered_for_program``),
    which the family code satisfies — no guessed 6-digit precision.
  * #4 ``who_its_for`` filled on every program with a PROGRAM-DISTINCT (distinct/total = 1.0)
    statement derived from each program's own field + credential level (12 hand-written
    flagship statements + a field-interpolated frame for the rest — never a degree-type
    template). The base ``apply()`` left the field empty catalog-wide.

Northwestern is private, so the public non-resident-tuition scalar (#2) does not apply, and
its master's / professional tuition was already verified per-tier (#3 — 71 bachelor's, 26
master's, 4 professional priced; 24 PhD funded $0). Because ``progprefbf1`` derived
program-preference rows while ``cip_code`` was still null, and ``backfill_program_preferences``
only fills EMPTY fields on existing rows, the corrected CIP would not reach the
program -> student field signal. So this DELETES unclaimed ``source="derived"`` preference
rows for Northwestern, then re-derives — the same recompute the UF / Michigan / Brown /
Emory / Purdue / UIUC / Rice / UW-Madison CIP repairs use. Direct apply (no lock-bounded
skip) so the data actually lands; verify-live on content.

Revision ID: nwcipwho1
Revises: uwmadcoa1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nwcipwho1"
down_revision = "uwmadcoa1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    northwestern_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == northwestern_profile.INSTITUTION_NAME)
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
