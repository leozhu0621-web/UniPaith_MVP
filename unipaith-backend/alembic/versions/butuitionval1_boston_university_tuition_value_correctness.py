"""Boston University — tuition VALUE-correctness (REPAIR_BACKLOG run 75 HIGH #1).

The prior tuition pass (#1058 / ``bunames1``) achieved tuition COVERAGE but not VALUE
correctness: it stamped BU's $69,870 full-time number on 182 graduate/professional rows
(the grader's "undergrad-sticker copy-down") and carried inconsistent PhD values (46 rows
at $0). This migration ships BU's REAL published 2025-26 rate per program — verified,
authoritative_2x (BU Student Accounting Services / Student Financials; U.S. News confirms
the Questrom full-time MBA at $69,870):

- BU charges ONE flat full-time rate ($69,870) for undergraduate AND most full-time
  graduate/professional programs (GRS, CAS, ENG, COM, CDS, SAR, Wheelock, SPH, GMS,
  Questrom MBA/MS, Law JD) — a documented BU policy, so a general full-time graduate row
  at $69,870 is its REAL published rate, NOT a copy-down of the undergrad sticker.
- Distinct published rates now stamped where they exist: SSW $40,352 · STH $24,648 · CFA
  School of Music $30,376 / MFA & visual/theatre $34,984 · MD $72,626 · DMD $99,680.
- Fully-funded research doctorates (PhD/DSc — full tuition scholarship + stipend), the
  MD/PhD MSTP, per-credit graduate certificates (total varies by credit count), and SDM
  advanced-education specialty programs (no single published annual figure) are recorded as
  honest omissions in each node's ``_standard.omitted`` — never the flat full-time number
  copied down. This removes the $0-says-free PhD rows AND the undergrad-sticker copy-down.

Re-applies ``bu_profile.apply()`` (idempotent) and re-derives program-preference rows.

Also UNIFIES the live dual Alembic head: ``mrguiucbu1`` (#1062) and ``jhutuition1`` (#1063)
both independently merge the same ``(bunames1, uiuctuition1)`` pair, so ``mrguiucbu1`` was
orphaned as a second head on ``main``. This migration's two-parent ``down_revision`` collapses
both into a single head (the auto-merge dual-head race, §8 step 5 — flagged for a human).

Revision ID: butuitionval1
Revises: mrguiucbu1, jhutuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "butuitionval1"
down_revision = ("mrguiucbu1", "jhutuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    applied = bu_profile.apply(session)
    if applied:
        inst = session.scalar(
            select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
