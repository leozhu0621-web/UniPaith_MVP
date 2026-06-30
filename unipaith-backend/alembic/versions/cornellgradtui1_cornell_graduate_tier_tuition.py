"""Cornell graduate-tier tuition residual → matcher budget scalar (M.Arch I + D.M.A. filled).

Closes the Cornell master's/professional-tier tuition residual (REPAIR_BACKLOG run 94 #1):
seven graduate rows previously shipped ``program.tuition`` null, so the CPEF matcher scored
their budget fit blind. Re-verified each — two PUBLISH a fillable annual/doctoral rate and
are now FILLED; the other five have no annual full-time basis and stay honestly omitted with
the verified total / per-credit rate preserved in ``cost_data``:

FILLED
  - **Master of Architecture (M.Arch I)** — a full-time RESIDENTIAL professional degree
    billed PER ACADEMIC YEAR at Cornell's endowed-Ithaca / Professional Degree Tier 1 rate
    (**$71,266**, 2025-26). AAP graduate tuition page + the Bursar both list the professional
    M.Arch at the same endowed-Ithaca professional rate as the M.Eng tier. It was previously
    (and wrongly) bucketed with the executive/per-credit omits.
  - **Doctor of Musical Arts (D.M.A.)** — a fully-funded Graduate-School DOCTORAL degree, not
    a self-pay professional program: every admitted student receives four guaranteed years of
    support (two Sage fellowships + two teaching assistantships covering full tuition + health
    insurance). The matcher budget input is therefore the published research-doctoral sticker
    (**$20,800**, Cornell Graduate School) with ``funded=True`` — never 0 (which the CPEF
    reads as "free") and never the undergraduate sticker copied down, mirroring the PhD rows.

OMIT-WITH-REASON (no annual full-time basis; ``program.tuition`` is consumed as ANNUAL by the
matcher, so a multi-year cohort TOTAL or per-credit rate would over-fire the budget veto)
  - **Executive MBA Americas** — fixed $198,234 program fee (5 installments / 17-month cohort)
  - **Executive M.H.A.** — flat $93,316 for the 18-month degree
  - **Executive M.P.A.** — flat $89,536 for the 18-month degree
  - **online M.S.L.S.** — $2,265/credit (30 credits / 5 part-time terms ≈ $67,950)
  - **hybrid M.Eng. Engineering Management** — $2,465/credit (30+ credits over 2-3 years)
Each verified total / per-credit rate is preserved in ``cost_data`` and the annual scalar is
recorded in the program node's ``_standard.omitted``. No number is guessed.

Re-applies ``cornell_profile.apply()`` (idempotent) and re-derives ``program_preferences`` so
the program -> student match reads the updated budget signal. No programs added/removed (221
unchanged), so the once-backfilled preference rows stay intact. Safe on a fresh/CI database
(no-op if Cornell absent).

Revision ID: cornellgradtui1
Revises: utagradtuition1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellgradtui1"
down_revision = "utagradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == cornell_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
