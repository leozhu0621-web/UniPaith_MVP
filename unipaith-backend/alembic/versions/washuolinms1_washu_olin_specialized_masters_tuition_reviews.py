"""WashU — Olin specialized-master's tuition + reviews (last matcher-core gap → gold)

Takes the Washington University in St. Louis catalog (58 programs across 8 schools) the rest
of the way to gold by closing its sole open REPAIR_BACKLOG defect:

  * #1 matcher-core master's tuition — the two Olin specialized master's billed at a flat
    PER-PROGRAM rate (MS in Finance, MS in Business Analytics) shipped tuition=None
    (omit-with-reason: "not separately stated in the university tuition release"). Olin
    DOES publish each program's rate on its Cost-Aid-Scholarships page, so per the
    matcher-core rule (a master's tier that publishes a rate is filled, not omitted) both
    now carry their verified published per-program annual rate:
      - MS in Finance  → $81,500 (Corporate Finance one-academic-year track; the STEM
        Quantitative / Wealth & Asset Management tracks run three semesters / $102,900).
      - MS in Business Analytics → $67,866 (two-semester academic year of the three-
        semester $101,799 program, billed $33,933/semester).
    The master's tuition tier goes 8/10 → 10/10 (no estimate; verified against the Olin
    Cost-Aid-Scholarships pages).

  * #5 external_reviews depth — the same two now-coverable Olin master's gain sourced,
    program-specific ``external_reviews`` (TFE Times ranked WashU's Master of Finance #3
    globally in 2025; STEM-designated tracks; AACSB faculty; cautions on cohort scale and
    St. Louis market) in the gold MBAn shape, joining the MBA / MSW / J.D. / M.D. flagships.

Everything else on the WashU tree is already gold: who_its_for is 100% program-distinct
(distinct/total == 1.0), cip_code is 100% in-sample, descriptions are anti-stub clean
(CERTIFIED_CLEAN), the campus gallery is >=4 photos, and the feed is live; funded
Graduate-School-of-Arts-&-Sciences doctorates keep funded=True / tuition=None.

Because the tuition the matcher's budget feature reads (and the reviewed program rows) are
rewritten, this follows the tuition-repair pattern (cf. ``uwwhofor1``): an idempotent
re-apply of ``washu_profile.apply()``, then for WashU's programs delete the stale derived
``program_preferences`` and re-derive them, bump ``Program.feature_version`` so the recompute
path re-embeds, and delete the cached ``MatchResult`` rows so ``GET /me/matches`` rescores
against the refreshed data. Claimed / first-party rows are never touched.

Revision ID: washuolinms1
Revises: uwwhofor1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import washu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "washuolinms1"
down_revision = "uwwhofor1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    washu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == washu_profile.INSTITUTION_NAME)
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
            session.execute(delete(MatchResult).where(MatchResult.program_id.in_(all_prog_ids)))
    session.flush()


def downgrade() -> None:
    pass
