"""Brown cip_code (REPAIR_BACKLOG #1) + master's tuition (#3) + who_its_for (#4) + reviews (#5)

Four matcher-core / universal-depth repairs on Brown's already-structurally-clean 57-program
catalog (real names, real departments, and field-specific descriptions were already clean; the
catalog STRUCTURE is untouched here):

  1. ``cip_code`` (matcher-core CIP join key to ref_majors + the field-66 vocabulary): Brown's
     ``apply()`` never stamped ``p.cip_code``, so the catalog shipped ``cip_code`` null
     fleet-wide and the matcher scored those programs field-blind. Now stamps the standard
     IPEDS CIP-2020 code for each program's field (``_CIP_BY_SLUG``, 57/57) — a published
     taxonomy lookup, never a guess.

  2. Master's tuition (#3): the four academic master's billed per course (Data Science Sc.M.,
     M.P.H., Watson MPA, Mechanical Engineering Sc.M.) shipped ``tuition`` null, so the matcher
     scored their budget-fit blind. They now carry Brown's OWN published annual tuition from its
     official Cost of Attendance by Program page (per-course rate × the program's standard
     full-time course load) — a published figure, never the undergraduate sticker copied down.
     The Watson MPA's duration is also corrected to its real one-year length.

  3. ``who_its_for`` (universal-depth field, run-84/86 rule): the catalog shipped this field 0%
     live because the ``apply()`` loop hard-set ``p.who_its_for = None``. It now stamps a
     per-program, field-specific applicant statement (``_WHO_BY_SLUG``, 57/57), each naming the
     applicant the program fits — never a classification stub. Restores the field to 100%.

  4. ``external_reviews`` depth (#5): adds program-specific, third-party-sourced reviews for the
     coverable graduate/professional programs (Data Science Sc.M., M.P.H., Watson MPA) beside the
     existing Warren Alpert M.D. review — each gathered from real coverage (Brown DSI / SPH /
     Watson official outcomes, GradReports, U.S. News), with cautions and resolvable sources.
     Programs with no program-specific third-party coverage keep their honest omission.

Idempotent: re-applies ``brown_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched. The
apply runs DIRECTLY (no lock-bounded self-skipping SAVEPOINT), so a failure fails the deploy
rather than silently stranding the data not-live.

Revision ID: browncipwho1
Revises: emorycipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import brown_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "browncipwho1"
down_revision = "emorycipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    brown_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == brown_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # Only clear DERIVED rows for UNCLAIMED programs — backfill_program_preferences skips
        # claimed programs, so deleting a claimed program's row here would strand it without
        # preference data (authority precedence: never touch first-party rows).
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
