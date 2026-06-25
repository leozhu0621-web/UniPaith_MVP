"""Georgia Tech matcher-core cip_code + public non-resident tuition scalar (REPAIR_BACKLOG #1 + #2)

Two matcher-core repairs on Georgia Tech, both choices between PUBLISHED/canonical values
(never a guess):

#1 cip_code STARVATION — the catalog shipped ``cip_code`` NULL on all 143 programs, so the
   CPEF matcher scored every program field-blind on the CIP join key (the interest/field
   signal that resolves a program to ``ref_majors`` + the field-66 vocabulary alongside the
   dense description embedding). Every program now carries a verified NCES CIP-2020 six-digit
   code (NN.NNNN) that (a) is the canonical code for that field, (b) exists in
   data/reference/ref_majors.jsonl (the matcher join target), and (c) sits within a CIP-4
   family Georgia Tech actually reports to IPEDS, cross-checked against the U.S. Dept. of
   Education College Scorecard field-of-study list for UNITID 139755. Coverage 0/143 -> 143/143.

#2 PUBLIC resident-tuition scalar MIS-SIGNAL — Georgia Tech is a public university, so it
   publishes two undergraduate stickers ($10,512 in-state / $32,938 out-of-state) and two
   graduate rates. The matcher's budget feature reads the flat ``program.tuition`` scalar
   (program_features -> matching.py budget breaker + affordability fit), NOT the residency-aware
   net-price estimator, so the previously-exposed IN-STATE scalar under-fired the over-budget
   veto 2.5-3.5x for the out-of-state + ALL-international applicant pool (the majority at a
   flagship public). The scalar now carries the NON-RESIDENT (out-of-state) rate for every
   residency-billed tier (bachelor's $32,938; standard graduate $32,146; each Bursar
   differential program its own published out-of-state rate), while the honest in-state rate
   stays in ``cost_data.breakdown`` (unchanged) and residency-flat online/professional totals
   (OMSCS, OMS Analytics, OMS Cyber, Executive MBAs, GTPE masters) keep their single published
   total. Funded research doctorates remain omitted-with-reason. This is a choice between two
   PUBLISHED numbers, never a guess.

Idempotent: re-applies ``georgia_tech_profile.apply()`` (sets cip_code + the non-resident
scalar on existing rows; adds/drops no programs) and re-derives the matcher's target-applicant
rows. Chains after ``uwcipscalar1`` (the head after the concurrent #1146 UW repair merged),
keeping ``main`` single-head.

Revision ID: gatechcip1
Revises: uwcipscalar1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gatechcip1"
down_revision = "uwcipscalar1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    georgia_tech_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == georgia_tech_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
