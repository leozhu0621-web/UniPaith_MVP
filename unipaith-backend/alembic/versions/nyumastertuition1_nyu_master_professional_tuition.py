"""NYU master's / professional tuition tier — fill the school-billed null rows.

Clears the residual master's-tier tuition gap that starved the CPEF matcher's graduate
budget-fit signal for NYU (REPAIR_BACKLOG #3): 194/232 master's rows carried tuition while
the 38 null rows were the school-billed professional + self-supporting master's (Stern,
Wagner, Meyers Nursing, Silver, Gallatin, Dentistry, Grossman) — each of which PUBLISHES its
own rate, so they were skipped knowable fields, not honest omissions.

Stamps each program's real published tuition, verified first-party 2026-06-25 against the
NYU Bursar 2025-26 schedule and the schools' own cost pages, cited per record (never the
undergraduate sticker, never guessed):

All figures are per-year (the matcher's tuition field is per-year), so multi-term executive /
cohort program totals are annualized by the published program length:

- Wagner $59,784 / Meyers Nursing $59,904 (+ the D.N.P.) / Gallatin $55,992 — the school's
  published per-credit ("per point") rate annualized at NYU's 24-credit full-time year. Silver
  M.S.W. $56,694 ($1,718/credit × the ~33-credit full-time pathway year).
- College of Dentistry M.S. (Biomaterials Science, Clinical Research) $41,994 (9 credits/sem).
- Stern, per program: Full-Time MBA $89,524 · Executive MBA (NY) $130,200 (=$238,700/22mo) ·
  Tech MBA $122,565 · Fashion & Luxury MBA $122,565 · Abu Dhabi EMBA $77,778 · TRIUM Global EMBA
  $156,060 (=$208,080/16mo) · MS Accounting $66,362 · MS Business Analytics & AI $95,900 · MS
  Fintech $70,240 · MS Management/MiM $46,332 · MS Quantitative Finance $49,824 · NYU Shanghai
  MS Data Analytics & Business Computing $49,824 · MS Marketing & Retail Science $49,824
  (36-credit programs at $2,076/credit).

Master's coverage 194/232 -> 227/232 (98%). The five still-omitted rows keep tuition
omitted-with-reason (no fabricated figure): the combined B.S./M.S. Accounting and the Global
Finance (NYU/HKUST) and Organization Management & Strategy Stern programs (no single published
per-year figure), and the two Grossman science master's NYU publishes no fixed dollar figure for.

Idempotent: re-applies ``nyu_profile.apply()`` and re-derives program-preference rows.

Revision ID: nyumastertuition1
Revises: uclamastertuition1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyumastertuition1"
down_revision = "uclamastertuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
