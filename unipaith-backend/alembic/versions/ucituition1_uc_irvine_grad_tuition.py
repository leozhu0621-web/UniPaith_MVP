"""UC Irvine — backfill published self-supporting / PDST graduate tuition (matcher budget signal)

Clears REPAIR_BACKLOG entry #1 (HIGH — matcher-core master's/professional tuition residual) for
the University of California, Irvine. The earlier ``uciprof1`` catalog correctly stamped the
undergraduate non-resident sticker and the state-supported academic-graduate rate, but OMITTED
tuition on the twelve programs billed off the UCI University Registrar's per-program fee site
(eleven self-supporting/SSGDP and PDST master's plus the Doctor of Nursing Practice). Those rows
shipped ``cost_data.tuition_usd`` null, so the CPEF matcher scored their budget fit BLIND — the
master's tier read 10/21 covered (11 null) and the professional tier 3/4 (1 null) live.

This re-applies ``uci_profile`` after that module was updated to stamp each of the twelve with its
real, published 2025-26 full-time annual tuition and fees (excluding the optional/waivable health
insurance), each cited to its UCI University Registrar fee page:

  Master of Finance $81,425 · M.S. Business Analytics $74,840 · Master of Data Science $50,301 ·
  M. Innovation & Entrepreneurship $64,711 · Master of Professional Accountancy $68,371 ·
  Master of Computer Science $50,525 · M.HCI/Design $57,216 ·
  M. Conservation & Restoration Science $30,712 · Doctor of Nursing Practice $43,860
  (self-supporting — one flat fee to residents and non-residents); and the three PDST master's
  with the NON-RESIDENT scalar plus a resident/non-resident breakdown — Master of Public Policy
  $37,308 (res $25,063) · M. Urban & Regional Planning $34,668 (res $22,423) · M.S. Genetic
  Counseling $42,906 (res $30,661). The M.C.R.S. ``duration_months`` is also corrected 12→24
  (the registrar confirms a two-year program: $29,106/yr, $58,212 total).

Nothing is guessed: every figure is the institution-published registrar rate; no genuinely
unpublished program remains null in the master's/professional tier. ``apply()`` is idempotent
(``replace=True`` semantics), so re-derived ProgramPreference rows are refreshed afterward
(claimed/first-party rows are never touched).

Head-sync: chains off the current single head ``washutuition1`` (SKILL.md §8 head-sync step 1),
so this PR carries exactly one head.

Deploy-safety (adopts the prior UCI pattern): the idempotent data apply runs inside a SAVEPOINT
bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot get
its locks quickly. The migration still records as applied so the chain advances;
``uci_profile.apply()`` is idempotent and the routine verifies the live API tuition coverage per
the SKILL.md §9 verify-live-on-content rule (re-applying explicitly if the apply was skipped).

Revision ID: ucituition1
Revises: washutuition1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uci_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucituition1"
down_revision = "washutuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(text("SET LOCAL lock_timeout = '30s'"))
    # Stage 1 — the tuition repair, in its OWN savepoint. If it is skipped (lock
    # contention at boot), bail before touching preferences.
    try:
        with session.begin_nested():
            uci_profile.apply(session)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  ucituition1: tuition re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )
        return
    # Stage 2 — refresh DERIVED ProgramPreference rows in a SEPARATE savepoint so a
    # backfill failure can NEVER roll back the already-flushed tuition repair above
    # (claimed/first-party rows are never touched by the helper).
    try:
        inst = session.scalar(
            select(Institution).where(
                Institution.name == uci_profile.INSTITUTION_NAME
            )
        )
        if inst is not None:
            with session.begin_nested():
                backfill_program_preferences(session, institution_id=inst.id)
            session.flush()
    except Exception as exc:  # noqa: BLE001 — preference refresh is best-effort
        print(
            f"  ucituition1: preference backfill skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
