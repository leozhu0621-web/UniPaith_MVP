"""UT Austin DNP + online CS/DS/AI master's — published program TOTAL as matcher budget scalar.

Closes the UT Austin master's/professional-tier tuition residual (REPAIR_BACKLOG #1):
four graduate programs that publish a single verified program TOTAL (and no separate
annual figure) previously shipped ``program.tuition`` null, so the CPEF matcher scored
their budget fit blind. Each now feeds its published TOTAL into the matcher's budget
scalar (``program.tuition``), while the editorial annual card field
(``cost_data.tuition_usd``) stays honestly omitted — the cost card shows a
``total_program_tuition`` (``tuition_period="total_program"``), so it never renders a
misleading "/yr":

1. **Doctor of Nursing Practice** (School of Nursing, post-MSN) — flat program total
   **$30,000** (45 credit hours over five semesters, ~$667/credit), the same regardless
   of residency. Verified first-party (UT School of Nursing DNP Tuition & Funding) and
   corroborated by a second independent source.
2. **MS in Computer Science (Online)**, **MS in Data Science (Online)**,
   **MS in Artificial Intelligence (Online)** (College of Natural Sciences / Computer &
   Data Science Online) — each a single published program total of **~$10,000**, the
   canonical, widely-quoted cost of these flexible part-time programs and the catalog's
   lowest-cost graduate option (so a null scalar lost the single strongest "very
   affordable" budget signal there is).

The Pharm.D. (calculator/PDF-only, not confirmable to two independent sources) and the
three specialized master's with no separately-published rate (MS Energy Management — not
admitting; MS Management; the IROM department row, marketed as the MSITM filled above)
remain honest omit-with-reason, recorded in each node's ``_standard.omitted``. PhD rows
keep their published graduate non-resident rate; no number is guessed.

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
