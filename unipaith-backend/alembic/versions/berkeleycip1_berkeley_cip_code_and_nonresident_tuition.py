"""Berkeley matcher-core cip_code + public non-resident tuition scalar (REPAIR_BACKLOG #1/#2/#3)

Three matcher-core repairs for UC Berkeley (UNITID 110635), all from already-published
or already-in-module verified figures — no fabrication:

* #1 — stamps the verified NCES CIP-2020 four-digit ``cip_code`` on all 231 programs
  (the CIP join key the CPEF matcher uses for the field/interest signal); 228 were
  already carried in the module's specs, three curated flagship undergrad majors
  (Data Science 30.70, Legal Studies 22.00, Public Health 51.22) were added, and the
  enrichment apply now assigns ``p.cip_code``. The Legal Studies addition dedups the
  federal-taxonomy-named "Non-Professional Legal Studies" row into the real
  "Bachelor of Arts in Legal Studies" (the orphan is removed by the program reconcile).
* #2 — Berkeley is PUBLIC, so the matcher's flat budget scalar (``program.tuition``) now
  carries the NON-RESIDENT rate (undergraduate $50,547 / graduate-academic $27,864) so
  the over-budget veto fires correctly for the out-of-state + international majority;
  the resident rate stays in ``cost_data.tuition_usd`` and the breakdown carries both.
* #3 — fills the three CED professional-master tuition nulls (M.Arch / M.C.P. / M.L.A.)
  with the verified CED published rate ($26,009), matching their -prof siblings.

Idempotent: re-applies ``berkeley_profile.apply()`` and re-derives program-preference rows.

Revision ID: berkeleycip1
Revises: utaustincip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleycip1"
down_revision = "utaustincip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    berkeley_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == berkeley_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # backfill_program_preferences only INSERTS missing rows + fills EMPTY keys; it
        # never recomputes pref_fields/pref_levels on the derived rows the fleet-wide
        # progprefbf1 backfill created while cip_code was still NULL. So delete this
        # institution's stale DERIVED rows first and re-derive them, so pref_fields
        # (= fields_offered_for_program(cip_code=...)) reflects the now-populated CIP
        # codes. Claimed / first-party rows are NEVER touched. (Mirrors gatechcip1.)
        prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        if prog_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(prog_ids),
                    ProgramPreference.source == "derived",
                )
            )
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
