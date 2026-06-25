"""NYU master's / professional tuition tier — fill the school-billed null rows.

Clears the residual master's-tier tuition gap that starved the CPEF matcher's graduate
budget-fit signal for NYU (REPAIR_BACKLOG #3): 194/232 master's rows carried tuition while
the 38 null rows were the school-billed professional + self-supporting master's (Stern,
Wagner, Meyers Nursing, Silver, Gallatin, Dentistry, Grossman) — each of which PUBLISHES its
own rate, so they were skipped knowable fields, not honest omissions.

Stamps each program's real published tuition, verified first-party 2026-06-25 against the
NYU Bursar 2025-26 schedule and the schools' own cost pages, cited per record (never the
undergraduate sticker, never guessed):

- Wagner $59,784 / Meyers Nursing $59,904 (+ the D.N.P.) / Silver M.S.W. $41,232 /
  Gallatin $55,992 — the school's published per-credit ("per point") rate annualized at
  NYU's 24-credit full-time year.
- College of Dentistry M.S. (Biomaterials Science, Clinical Research) $41,994 (9 credits/sem).
- Stern, per program: Full-Time MBA $89,524 · Executive MBA (NY) $238,700 · Tech MBA
  $122,565 · Fashion & Luxury MBA $122,565 · Abu Dhabi EMBA $87,500 · TRIUM Global EMBA
  $208,080 · MS Accounting $66,362 · MS Business Analytics & AI $95,900 · MS Fintech $87,800 ·
  MS Management (MiM) $77,220 · MS Quantitative Finance $49,824.

Master's coverage 194/232 -> 225/232 (97%). The seven still-omitted rows keep tuition
omitted-with-reason (no fabricated figure): five Stern programs whose tuition NYU publishes
only after enrollment (the NYU Shanghai / HKUST joint programs and the combined B.S./M.S.),
and the two Grossman science master's NYU publishes no fixed dollar figure for.

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
