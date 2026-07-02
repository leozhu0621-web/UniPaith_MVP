"""Case Western Reserve — correctness fixes from the #1277 Codex review (re-apply)

Follow-up to casewestprof1 addressing three verified per-program correctness defects
surfaced by the automated review on PR #1277:

1. Dental (D.M.D.) and Physician Assistant (M.S.) programs were assigned the
   medical-school application template (AMCAS + MCAT). They now carry their own
   centralized application systems — AADSAS + DAT for the D.M.D., CASPA for the PA.
2. The Master of Science in Physician Assistant Studies was typed ``professional``,
   which kept a master's-titled degree out of the search service's master's-tier
   filter (``_DEGREE_MAP`` maps "master"/"ms" → ``masters``). It is now typed
   ``masters`` (its real conferred degree), so it surfaces in master's-level search.
3. The S.J.D. (research law doctorate) and D.M.A. (performance doctorate) sit in the
   ``phd`` degree bucket but are NOT covered by a verifiable full-tuition-waiver
   funding convention, so the funded-PhD fallback was falsely marking them
   ``tuition=0`` / ``funded=True`` (telling students they are free). Their tuition is
   now honestly omitted-with-reason.

Re-applies the (corrected) ``case_western_profile.apply(session)`` idempotently and
re-derives ``program_preferences``; because apply() rewrites the whole catalog, this
brings production to the corrected 206-program state whether or not casewestprof1's
data apply landed. Deploy-safe: runs inside a ``lock_timeout``-bounded SAVEPOINT that
is skipped-and-logged rather than hanging container boot; still records as applied so
the alembic chain advances.

Revision ID: casewestfix1
Revises: casewestprof1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import case_western_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "casewestfix1"
down_revision = "casewestprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            case_western_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == case_western_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                # Drop derived (non-claimed) preferences so they are re-derived against the
                # corrected degree_type / requirements, then re-derive.
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
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(f"  casewestfix1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
