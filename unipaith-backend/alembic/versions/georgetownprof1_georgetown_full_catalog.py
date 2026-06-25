"""Georgetown University — enrich the empty-description seed to a full gold catalog

Clears the top REPAIR_BACKLOG CRITICAL (#2): the Georgetown flagship seed shipped 5
programs each with an EMPTY ``description_text`` (a blank student page + zero matcher
embedding) and 0% tuition / 0% who_its_for / institution feeds unset.

This replaces the 5 stubs with the full, verified Georgetown degree catalog — 190 real,
distinctly-named programs across the ten degree-granting schools (College of Arts &
Sciences, Walsh School of Foreign Service, McDonough School of Business, McCourt School
of Public Policy, School of Nursing, School of Health, School of Medicine / Biomedical
Graduate Education, Law Center, Graduate School of Arts & Sciences, School of Continuing
Studies). Every program carries:

  * a researched, field-specific ``description_text`` (Bulletin / official-site sourced;
    anti-stub gold-clean — verbatim/shared-body/classification/template-slot/scrape-debris
    all 0, baselined to gold MIT);
  * the IPEDS ``cip_code`` (matcher field/interest join key) and a universal ``who_its_for``;
  * the real owning ``department`` and ``delivery_format``;
  * published 2025-26 tuition — the undergraduate sticker fills the entire bachelor's tier
    (100%), JD / MD / full-time MBA / full-time LL.M. / McCourt + Graduate-School per-credit
    masters carry their verified published rate, and per-credit-billed grad rows + funded
    PhDs are honest omit-with-reason (never the undergrad sticker copied down);
  * ``content_sources`` (THE FEED RSS + the LiveWhale events iCal, both verified live) on the
    institution, every school, and every program.

Institution stats (admissions funnel, SAT/ACT, demographics, retention, endowment, rankings)
are filled from the Common Data Set / NCES / College Scorecard; a 4-photo verified Wikimedia
gallery is kept. All values are verified-or-omitted and stamped in ``georgetown_profile``.

Match-side: backfills a derived ProgramPreference row per program (skips claimed rows).

Deploy-safety (adopts the dartfinish1 pattern): the idempotent data apply runs in a
SAVEPOINT bounded by ``lock_timeout`` so a contended table never hangs container boot; on
any error it is SKIPPED (recorded as applied so the chain advances), and the idempotent
``georgetown_profile.apply()`` re-applies next routine run.

Revision ID: georgetownprof1
Revises: sixheadmerge1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgetown_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "georgetownprof1"
down_revision = "sixheadmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            # Drop this institution's stale DERIVED preference rows FIRST (the fleet-wide
            # progprefbf1 backfill created them on the 5 empty-slug seed stubs before this
            # catalog existed). Removing them lets apply() delete those stubs cleanly rather
            # than only unpublishing them; claimed / first-party rows are NEVER touched.
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == georgetown_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                seed_prog_ids = session.scalars(
                    select(Program.id).where(Program.institution_id == inst.id)
                ).all()
                if seed_prog_ids:
                    session.execute(
                        delete(ProgramPreference).where(
                            ProgramPreference.program_id.in_(seed_prog_ids),
                            ProgramPreference.source == "derived",
                        )
                    )
            georgetown_profile.apply(session)
            if inst is not None:
                # Re-derive a grounded target-applicant row per program now that cip_code /
                # class data are populated (skips any claimed rows).
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  georgetownprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
