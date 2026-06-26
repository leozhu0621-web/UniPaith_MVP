"""Purdue cip_code (REPAIR_BACKLOG #3) + who_its_for (#6) + non-resident tuition scalar (#4)

Three matcher / universal-depth repairs on Purdue's already-real 172-program catalog (names,
departments, and field-specific descriptions were already structurally clean fleet-wide; the
catalog STRUCTURE is untouched here):

  1. ``cip_code`` (matcher-core CIP join key to ref_majors + the field-66 vocabulary): Purdue's
     ``apply()`` never stamped ``p.cip_code`` even though every catalog spec already carries the
     IPEDS CIP it uses for the breadth cross-check, so the catalog shipped ``cip_code`` null
     fleet-wide and the matcher scored those programs field-blind. Now stamps ``spec["cip"]`` on
     all 172 rows (one assignment, no new research) — ~100% coverage.

  2. ``who_its_for`` (universal-depth field, run-84/86 rule): the catalog shipped this field 0%
     live. It now stamps a per-program, field-specific applicant statement from
     ``purdue_who.WHO_BY_SLUG`` (172/172), each derived from the program's own field + credential
     level — never a classification stub, no fabricated named units. Restores the field to ~100%.

  3. Public-university tuition scalar (run-83 rule): the CPEF budget veto reads the flat
     ``program.tuition`` scalar for EVERY applicant regardless of residency, so a resident-rate
     scalar under-fires the budget veto for the out-of-state + ALL international pool (the majority
     at a flagship public). The scalar now carries the NON-RESIDENT published rate at every tier it
     was previously the resident rate — undergrad $9,992 -> $28,794, general graduate the same,
     CSE/engineering -> $29,918, Daniels -> $41,210, Polytechnic -> $29,366, MS-SLP -> $30,294,
     PharmD -> $41,532, DVM -> $47,759 (all verified against the 2024-25 Purdue Bursar schedules) —
     while ``cost_data.breakdown`` still preserves BOTH the resident and non-resident rate (a choice
     between two PUBLISHED numbers, never a guess). The funded-PhD $0 is unchanged.

Idempotent: re-applies ``purdue_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched. The
apply runs DIRECTLY (no lock-bounded self-skipping SAVEPOINT), so a failure fails the deploy
rather than silently stranding the data not-live.

Revision ID: purduewhotuition1
Revises: aiturnagents1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "purduewhotuition1"
down_revision = "aiturnagents1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    purdue_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == purdue_profile.INSTITUTION_NAME)
    )
    if inst is not None:
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
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
