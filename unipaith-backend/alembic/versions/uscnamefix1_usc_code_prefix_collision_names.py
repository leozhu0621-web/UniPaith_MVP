"""USC de-fabricate `_CODE_PREFIX` collision + redundant program names.

Re-applies ``usc_profile.apply()`` after fixing a structural name-realness defect the
run-94 grader's name scan missed (REPAIR_BACKLOG structure / SKILL.md miss #2). USC's
build derives each master's/doctoral credential from the slug's trailing code via
``_CODE_PREFIX``, but several USC codes COLLIDE across different degrees, so the wrong
designation rendered glued to the real field — student-facing nonsense:

  * ``mcm`` → "Master of Communication Management" stamped onto **Construction Management**
  * ``mpap`` → "Master of Public Art Studies" onto the **Physician Assistant** program
  * ``mcl`` → "Master of Communication Law Studies" onto **Comparative Law**
  * ``mpd`` → "Master of Public Diplomacy" onto **Planning and Development Studies**
  * ``mbs`` → "Master of Business for Veterans" onto **Building Science**
  * plus "Doctor of Liberal Arts in Longevity Arts and Sciences" (real: D.L.A.S.)

and ~22 redundant "Master of X in X" doublings ("Master of Accounting in Accounting",
"Master of Public Health in Public Health"). Each is resolved to USC's real conferred
degree name (verified on catalogue.usc.edu / the owning school's site) via
``_PROGRAM_NAME_OVERRIDES``; the field-echo departments on those rows are mapped to the
real owning USC school. Three concentration-variant members are re-anchored onto their
renamed base so they re-collapse into ``tracks`` (miss #2). No field/CIP/description
content changed — only the credential label + owning unit. ``usc_cip_who`` gained the
new single-designation names in ``SPECIAL`` so cip_code / who_its_for still resolve
(who distinctness stays 1.0).

Because the rendered ``program_name`` feeds the dense ``description_text`` embedding
context and the program-side match signal, the unclaimed ``source="derived"``
ProgramPreference rows are re-derived and cached MatchResult rows for USC programs are
marked stale so GET /me/matches rescores against the corrected names.

Revision ID: uscnamefix1
Revises: ucdreviews1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uscnamefix1"
down_revision = "ucdreviews1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    usc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == usc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        all_prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        unclaimed_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if unclaimed_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(unclaimed_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
        if all_prog_ids:
            session.execute(
                Program.__table__.update()
                .where(Program.id.in_(all_prog_ids))
                .values(feature_version=Program.feature_version + 1)
            )
            session.execute(
                delete(MatchResult).where(MatchResult.program_id.in_(all_prog_ids))
            )
    session.flush()


def downgrade() -> None:
    pass
