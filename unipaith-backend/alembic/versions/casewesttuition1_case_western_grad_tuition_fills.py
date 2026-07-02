"""Case Western Reserve — fill published graduate/professional tuition wrongly omitted

REPAIR_BACKLOG #1 (matcher-core master's/professional-tier tuition residual). The
206-program CWRU catalog was structurally clean (real names, distinct ``who_its_for``,
``cip_code`` filled, ≥4 photos, live news feed) but shipped 13 master's/professional
programs with a NULL ``tuition`` recorded as omit-with-reason — even though CWRU DOES
publish a verifiable rate for each, so the CPEF matcher scored their budget fit blind.
Each rate below was re-verified against CWRU's first-party student-accounts pages, at the
CURRENT (2026-27) rate a prospective applicant pays where the school publishes it (the
matcher consumes ``program.tuition`` as the current-cycle budget signal):

- Six postdoctoral M.S.D. dental specialties (Orthodontics, Periodontics, Endodontics,
  Pediatric Dentistry, Oral & Maxillofacial Surgery, Oral Medicine) → the general
  graduate-dental rate $35,838/semester (12+ credits, 2026-27) → full-time year x2 =
  $71,676 (School of Dental Medicine student-accounts page).
- Physician Assistant M.S. → $47,022/year (Class of 2028; tuition stated separately from
  fees: $47,022 + $47,022 + $15,674 summer = $109,718 total program tuition).
- School of Law: M.C.R.M. + Patent Practice M.A. → the 10+ credit full-time flat
  $24,400/semester (2026-27) → $48,800/year; Master of Legal Studies (ML) + the non-funded
  S.J.D. law doctorate → the general Law full-time flat $33,300/semester → $66,600/year
  (both grouped in the priced "SJD and Master of Laws (LLM and ML)" row).
- Weatherhead M.S. Leadership & Organizational Change → the ENTERING-cohort rate
  $1,750/credit x24 = $42,000/year (2026-27); M.S. Business Analytics & Intelligence →
  the published full-time total $46,575/year ($1,725/credit x 13.5 credits/term x2).

Only the M.A. Financial Integrity (the one Law master's absent from the price table) and
the D.M.A. performance doctorate (no published per-program rate) keep an honest
omit-with-reason. The events feed url was also normalized to its resolvable HTTPS
Google-Calendar form. (2026-07-02 Codex PR review corrected the four value/coverage points
above — current-year dental rate, entering MSLOC rate, MBAI credit load, and the ML/SJD
fills — verified against the source before applying.)

Re-applies the (corrected) ``case_western_profile.apply(session)`` idempotently and
re-derives ``program_preferences``; because apply() rewrites the whole catalog, this
brings production to the corrected tuition state whether or not the prior data applies
landed. Deploy-safe: runs inside a ``lock_timeout``-bounded SAVEPOINT that is
skipped-and-logged rather than hanging container boot; still records as applied so the
alembic chain advances (the live-API content re-query after deploy is the real gate).

Revision ID: casewesttuition1
Revises: lehighfix1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import case_western_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "casewesttuition1"
down_revision = "lehighfix1"
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
        print(f"  casewesttuition1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
