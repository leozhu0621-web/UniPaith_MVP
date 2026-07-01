"""Princeton who_its_for (REPAIR_BACKLOG #3b / SKILL.md miss #3b — who_its_for distinctness)

A single depth repair on Princeton's already-real 43-program catalog (names, departments,
descriptions, ``cip_code``, tuition, photos, feeds, and coverable reviews were already gold;
structure and every other dimension are untouched):

  ``who_its_for`` (universal-depth field, run-89 distinctness rule): Princeton's ``apply()``
  loop resolved ``p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE``, but ``_WHO_BY_SLUG``
  covered only 2 flagship slugs, so 41 of 43 programs shipped the SAME generic ``_WHO_BASELINE``
  string — 3 distinct values live (distinct/total ≈ 0.07), the type-gaming the rule forbids (a
  Chemistry major and a History major read identically). ``_WHO_BY_SLUG`` now carries a
  per-program, field-specific applicant statement for all 43 (subject · who it fits · typical
  next step) — derived from each program's own field and Princeton's published department
  character, never a degree-type template, no fabricated named units/rankings. Restores the
  field to 43/43 distinct (distinct/total = 1.0).

Idempotent: re-applies ``princeton_profile.apply()`` (updates existing rows by slug) and
re-derives DERIVED program preferences so ``pref_*`` reflect the catalog; claimed/first-party
rows are never touched. Direct apply (no lock-timeout SAVEPOINT) — the 43-row update is light,
so the apply genuinely runs in prod (avoids the self-skipping-migration stranding, FLAG #1).

Revision ID: princetonwho1
Revises: gatechwho1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "princetonwho1"
down_revision = "gatechwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    princeton_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == princeton_profile.INSTITUTION_NAME)
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
