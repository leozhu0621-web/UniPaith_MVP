"""UT Austin matcher-core cip_code + public non-resident tuition scalar + grad tuition fills

Three matcher-core repairs on The University of Texas at Austin, every value a choice
between PUBLISHED/canonical numbers (never a guess):

#1 cip_code STARVATION — the catalog shipped ``cip_code`` NULL on all 338 programs, so the
   CPEF matcher scored every program field-blind on the CIP join key (the interest/field
   signal that resolves a program to ``ref_majors`` + the field-66 vocabulary alongside the
   dense description embedding). Every program now carries its standard IPEDS CIP-2020
   four-digit code, keyed on the catalog field and cross-checked against the U.S. Dept. of
   Education College Scorecard field-of-study list for UNITID 228778. Coverage 0/338 ->
   338/338.

#2 PUBLIC resident-tuition scalar MIS-SIGNAL — UT Austin is a public university, so it
   publishes a resident and a much-higher non-resident sticker per tier. The matcher's budget
   feature reads the flat ``program.tuition`` scalar (program_features -> matching.py budget
   breaker + affordability fit), NOT the residency-aware net-price estimator, so the
   previously-exposed IN-STATE scalar under-fired the over-budget veto 2.5-3.5x for the
   out-of-state + ALL-international applicant pool (the majority at a flagship public). The
   scalar now carries the NON-RESIDENT (out-of-state) rate for every residency-billed tier
   (bachelor's $44,908; standard graduate $22,954; MBA $61,214; LL.M. $49,490; Law J.D.
   $56,822; M.D. $37,138), while BOTH rates always stay in ``cost_data.breakdown`` (the cost
   card shows the resident basis, unchanged). This is a choice between two PUBLISHED numbers,
   never a guess.

#3 master's-tier tuition residual (REPAIR_BACKLOG #3) — six McCombs specialized master's
   that previously omitted tuition now carry their official published one-year program total
   as the (non-resident) budget scalar, each read from that program's own McCombs tuition
   page (verified 2026-06-25): MPA $70,453, MS Business Analytics / Finance / Marketing / IT
   & Management $58,000, MS Technology Commercialization $58,500 (flat). The post-MSN DNP's
   verified $30,000 flat program total is recorded in ``cost_data.total_program_tuition``
   (its annual scalar stays omitted — the total spans five semesters). Programs with no
   official published figure (MS Accounting, MS Management, MS Energy Management which is not
   admitting, IROM, PharmD, AuD, and the multi-year online MSCS/MSDS/MSAI) keep their honest
   omit-with-reason. master's tuition coverage 115/128 -> 121/128; the residual is legitimate
   omit-with-reason.

Idempotent: re-applies ``ut_austin_profile.apply()`` (sets cip_code + the non-resident scalar
+ the grad tuition fills on existing rows; adds/drops no programs) and re-derives the matcher's
target-applicant rows so pref_fields reflect the now-populated CIP codes (the fleet-wide
progprefbf1 backfill ran while cip_code was NULL). Chains after ``gatechcip1``, keeping
``main`` single-head.

Revision ID: utaustincip1
Revises: gatechcip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utaustincip1"
down_revision = "gatechcip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ut_austin_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ut_austin_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # backfill_program_preferences only INSERTS missing rows + fills EMPTY keys; it never
        # recomputes pref_fields/pref_levels on the derived rows the fleet-wide progprefbf1
        # backfill created while cip_code was still NULL. So delete this institution's stale
        # DERIVED rows first and re-derive them, so pref_fields (= fields_offered_for_program(
        # cip_code=...)) reflects the now-populated CIP codes. Claimed / first-party rows are
        # NEVER touched. (Mirrors gatechcip1 / uclacip2.)
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
