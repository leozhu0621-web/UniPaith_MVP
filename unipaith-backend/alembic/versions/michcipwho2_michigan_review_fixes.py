"""Michigan matcher-core follow-up — review fixes for michcipwho1.

Corrects three defects found in code review of #1186:
  * two non-standard CIP codes replaced with real CIP-2020 codes present in
    ref_majors (International Studies 05.0901 -> 30.2001; Molecular and Cellular
    Pathology 26.0410 -> 26.0406);
  * the phd-tier highlights no longer advertise Rackham funding on a PAID/applied
    doctorate (D.Eng., DrPH) that is not a funded research Ph.D. (no-fabrication);
  * the migration now DELETES unclaimed ``source="derived"`` ProgramPreference rows
    before re-deriving, so the corrected ``cip_code`` reaches the program -> student
    field signal (the fleet ``progprefbf1`` backfill created those rows while Michigan
    ``cip_code`` was still null, and ``backfill_program_preferences`` only fills empty
    fields on existing rows — matching the brown/emory/purdue/ucla CIP repairs).

Re-applies ``michigan_profile.apply()``. Direct apply (no lock-bounded skip).

Revision ID: michcipwho2
Revises: michcipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "michcipwho2"
down_revision = "michcipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == michigan_profile.INSTITUTION_NAME)
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
