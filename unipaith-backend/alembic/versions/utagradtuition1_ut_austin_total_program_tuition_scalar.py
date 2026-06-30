"""UT Austin DNP flat annual tuition → matcher budget scalar (professional tier filled).

Closes the UT Austin professional-tier tuition residual (REPAIR_BACKLOG #1): the
post-MSN **Doctor of Nursing Practice** previously shipped ``program.tuition`` null, so
the CPEF matcher scored its budget fit blind. The DNP bills a published FLAT per-semester
rate — **$6,000 per semester (9 credit hours), the same for residents and non-residents**
(verified first-party: UT School of Nursing DNP Tuition & Funding; five consecutive
semesters Fall1/Spring1/Summer1/Fall2/Spring2 = $30,000 / 45 credit hours). Since
``program.tuition`` is consumed as ANNUAL tuition by the matcher
(``program_features`` -> ``tuition_usd_per_year``; ``matching`` budget veto) and rendered
"/yr" by the UI, the scalar carries the conventional ANNUAL sticker —
``$6,000 × 2 standard Fall+Spring semesters = $12,000/yr, flat`` — exactly how every other
annual rate in this module is constructed. The full $30,000 program total is preserved in
``cost_data.total_program_tuition`` for the editorial cost card.

The online CS/DS/AI master's publish only a single FLEXIBLE multi-year program TOTAL
(~$10,000) with no per-semester or annual basis, so their annual scalar is honestly
omitted (recorded in ``_standard.omitted``; total kept in ``cost_data``) rather than stuff
a multi-year total into the annual field — which would over-fire the budget veto and render
"/yr" (no consumer honors ``tuition_period``). The Pharm.D. (calculator/PDF-only,
unverifiable to two independent sources) and three specialized master's with no
separately-published rate (MS Energy Management — not admitting; MS Management; the IROM
department row, marketed as the MSITM filled above) likewise remain honest
omit-with-reason. PhD rows keep their published graduate non-resident rate; no number is
guessed.

Re-applies ``ut_austin_profile.apply()`` (idempotent) and re-derives
``program_preferences`` so the program -> student match reads the updated budget signal.
No programs added/removed (338 unchanged), so the once-backfilled preference rows stay
intact. Safe on a fresh/CI database (no-op if UT Austin absent).

Revision ID: utagradtuition1
Revises: mitucdmrg1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utagradtuition1"
down_revision = "mitucdmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ut_austin_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
