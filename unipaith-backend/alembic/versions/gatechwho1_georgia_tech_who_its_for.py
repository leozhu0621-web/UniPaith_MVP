"""Georgia Tech who_its_for (REPAIR_BACKLOG #3a / SKILL.md miss #2 universal-depth field)

A single depth repair on Georgia Tech's already-real 143-program catalog (names, departments,
descriptions, ``cip_code``, the per-credential tuition tiers, photos, and feeds were already
gold; structure and every other dimension are untouched):

  ``who_its_for`` (universal-depth field, run-84/86 rule): the Georgia Tech ``apply()`` loop
  hard-set ``p.who_its_for = None``, so the field shipped 0% live — a depth FAILURE, never a
  legitimate omission (every program can state the applicant it fits). It now stamps a
  per-program, field-specific applicant statement from ``georgia_tech_profile._WHO_BY_SLUG``
  (143/143), each derived from the program's own published field/level/audience material
  (subject · who it fits · typical next step) — never a degree-type template (a CS PhD and a
  Public-Policy PhD name different applicants), no fabricated named units. Build-time gates
  assert 100% coverage AND program-distinctness (distinct/total == 1.0), so the type-gaming
  the rule forbids cannot ship. Restores the field to 100% distinct.

Idempotent: re-applies ``georgia_tech_profile.apply()`` (replace) and re-derives DERIVED
program preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched.

Revision ID: gatechwho1
Revises: ndwho1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gatechwho1"
down_revision = "ndwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    georgia_tech_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == georgia_tech_profile.INSTITUTION_NAME)
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
