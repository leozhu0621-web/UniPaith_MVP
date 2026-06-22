"""Georgia Tech published graduate / professional tuition backfill (REPAIR_BACKLOG #2)

Clears the master's / professional-tier tuition STARVATION the catalog aggregate hid:
the bachelor's tier shipped 100% but the master's tier was 2/55 and the professional
tier 0/8 (matcher scored graduate budget-fit blind). Georgia Tech is a public university
whose graduate tuition is PUBLISHED — the University System of Georgia Board of Regents
sets a standard full-time graduate rate that applies to every graduate program except the
ones on the Bursar's differential-tuition list, each of which carries its own published
rate. Every figure is verified against the official CURRENT "Fall 2026 Tuition and Fee
Rates per Semester" Bursar schedule (full-time 12+ credit rate × two semesters, the same
in-state basis the undergraduate row uses and the basis the matcher reads as annual
tuition; out-of-state carried in cost_data.breakdown):

  * standard graduate rate -> $14,560 in-state / $32,146 out-of-state (the ~40 master's
    and the two unlisted professional programs not on the differential list);
  * Bursar differential programs -> their own distinct published rates (Full-Time MBA
    $30,548, on-campus MS Analytics $30,236, MSQCF $18,206, MSECE $17,056, MSHCI $16,630,
    MSROBO $16,622, MSBINF $17,100, MSSCE $17,150, M.Arch $18,692, MCRP $17,506, MSGIST
    $17,506, MID $18,692, MSMT $18,136, MSUD $18,692, MSBCFM $20,204 — annual in-state);
  * the three online OMS degrees keep their verified per-credit program totals (OMSCS
    $7,000, OMS Analytics $12,348, OMS Cybersecurity $11,936 = 32 cr x $373/cr Fall 2026).

Result per tier: master's 2/55 -> 55/55, professional 0/8 -> 3/8. The standard rate
($14,416) is distinct from the undergraduate sticker ($10,512) and the differential
programs each carry distinct rates, so no undergrad sticker is copied down a heterogeneous
tier (tuition VALUE-realness). Legitimately OMITTED-with-reason (no single published annual
figure / funding waives tuition, never guessed): the 39 funded research PhDs, the two
Executive MBAs (billed $21,775 per residence term), and the three GTPE professional
master's (program-specific per-credit rates) — each recorded in that program's
``_standard.omitted``.

Idempotent: re-applies ``georgia_tech_profile.apply()`` (which prunes nothing here — no
rows added or dropped, only tuition / cost_data set) and re-derives the matcher's
target-applicant rows. Chains after ``cornellcip2`` (the latest head at merge time, after
the concurrent #1090 Harvard and #1093 Cornell repairs), keeping ``main`` at a single head.

Revision ID: gatechgradtuition1
Revises: cornellcip2
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gatechgradtuition1"
down_revision = "cornellcip2"
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
