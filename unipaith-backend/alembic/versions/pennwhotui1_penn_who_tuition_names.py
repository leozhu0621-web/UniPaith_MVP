"""Penn who_its_for distinctness + placeholder-name dedupe + Fels MPA tuition

A single whole-university depth repair on Penn's already-real 180-program catalog (names,
departments, descriptions, ``cip_code``, photos, feeds, and coverable reviews were already
gold; structure and every other dimension are untouched). Three defects, all REPAIR_BACKLOG
entries on the one worst-off catalog, cleared together:

  1. ``who_its_for`` (REPAIR_BACKLOG #3b, run-89 distinctness rule): Penn's ``apply()`` loop
     resolved ``p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE``, but ``_WHO_BY_SLUG``
     covered only 12 flagship slugs, so ~166 programs shipped the SAME generic ``_WHO_BASELINE``
     string (distinct/total ≈ 0.05 live — the type-gaming the rule forbids: a CS Ph.D. and a
     Public-Policy row read identically). ``_WHO_BY_SLUG`` now carries a per-program,
     field-specific applicant statement for all 178 shipping programs (subject · who it fits ·
     next step), derived from each program's own field and credential level — never a
     degree-type template, no fabricated named units/rankings. Restores the field to
     178/178 distinct (distinct/total = 1.0).

  2. Placeholder-name dedupe (REPAIR_BACKLOG #4a): the two Scorecard professional-LEVEL rows
     for Law (CIP 22.01) and Veterinary Medicine (01.80) rendered as the generic degree-TYPE
     placeholder ``Professional program in {field}`` — duplicates of Penn's real Juris Doctor
     (JD) and Doctor of Veterinary Medicine (VMD) flagships, which already ship correctly
     named. They are DROPPED via ``_ROLLUP_LEVEL_DROP`` (a dedupe, not a rename), mirroring the
     already-dropped Dental/Med professional rows.

  3. Matcher-core tuition (REPAIR_BACKLOG #1): the Fels Institute M.P.A. — a one-year,
     per-course-unit professional degree with a published rate ($7,322/c.u., 2026-27) — shipped
     ``tuition=null`` (budget-blind). It is now filled at the full-time academic-year rate
     ($58,576) and named by its conferred M.P.A. designation. The remaining null graduate
     tuitions (the per-c.u. LL.M./ML law masters, the Annenberg submatriculation M.A., the
     funded/specialized Perelman masters, per-credit certificates, and funded Ph.D.s) stay
     honestly omitted-with-reason — never guessed.

Idempotent: re-applies ``penn_profile.apply()`` (updates existing rows by slug, reconciles the
two dropped placeholders) and re-derives DERIVED program preferences so ``pref_*`` reflect the
catalog; claimed/first-party rows are never touched. Direct apply (no lock-timeout SAVEPOINT) —
the update is light, so the apply genuinely runs in prod (avoids the self-skipping-migration
stranding, FLAG #1).

Revision ID: pennwhotui1
Revises: uwfeetuition1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "pennwhotui1"
down_revision = "uwfeetuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    # Delete DERIVED program preferences for Penn's existing rows BEFORE apply(), so the two
    # placeholder rows apply() reconciles away have no ProgramPreference dependents and are
    # genuinely DELETED (not merely unpublished) — ``_program_has_dependents`` scans every FK
    # into ``programs.id``, which includes ``program_preferences`` from the prior fleet
    # backfill. A row that a student actually references (a saved list, application, or match)
    # still trips a real dependent and is safely unpublished instead. First-party/claimed
    # preferences are left untouched (only ``source == "derived"`` is cleared).
    inst = session.scalar(
        select(Institution).where(Institution.name == penn_profile.INSTITUTION_NAME)
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
    penn_profile.apply(session)
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
