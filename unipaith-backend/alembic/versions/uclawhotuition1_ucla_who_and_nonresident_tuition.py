"""UCLA who_its_for (REPAIR_BACKLOG #6) + non-resident tuition scalar (REPAIR_BACKLOG #4)

Two matcher/depth repairs on UCLA's already-real 372-program catalog (names, departments,
descriptions, and ``cip_code`` were already gold; structure is untouched):

  1. ``who_its_for`` (universal-depth field, run-84/86 rule): UCLA's ``apply()`` loop hard-set
     ``p.who_its_for = None`` on every program, so the field shipped 0% live. It now stamps a
     per-program, field-specific applicant statement from ``ucla_profile._WHO_BY_SLUG`` (372/372),
     each derived from the program's own verified description + field + credential level — never a
     classification stub, no fabricated named units. Restores the field to ~100%.

  2. Public-university tuition scalar (run-83 rule): the CPEF budget veto reads the flat
     ``program.tuition`` scalar for EVERY applicant regardless of residency, so a resident-rate
     scalar under-fires the budget veto for the out-of-state + ALL international pool (the majority
     at a flagship public). The scalar now carries the NON-RESIDENT (out-of-state) published rate
     at every level it was previously the resident rate — undergrad $15,202 -> $49,402, academic
     graduate / on-campus certificate $21,115 -> $36,297 — while ``cost_data.breakdown`` still
     preserves BOTH the resident and non-resident rates (a choice between two PUBLISHED numbers,
     never a guess). Professional / self-supporting flat program fees and the funded-PhD $0 are
     unchanged.

Idempotent: re-applies ``ucla_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched.

Revision ID: uclawhotuition1
Revises: uciprof1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclawhotuition1"
down_revision = "uciprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ucla_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucla_profile.INSTITUTION_NAME)
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
