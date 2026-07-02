"""University of Rochester — fill the matcher-core graduate tuition residual (REPAIR_BACKLOG #1)

``rochreapply1`` (#1282) landed Rochester's tuition/delivery/funding corrections but left the
per-credit-billed graduate tiers omitted: the master's tier shipped 21 of 52 rows ``tuition``
null (40%) and the professional tier 6 of 7 (86%), so the CPEF budget feature scored those
programs' affordability BLIND. Per SKILL §1 (a whole master's / professional tier >20% null
beside filled peers is matcher STARVATION, not an honest omission — stamp the published rate),
this re-applies ``rochester_profile.py`` with every remaining fillable graduate row priced from
the school's VERIFIED published rate × the program's VERIFIED published credit requirement (or
the school's published full-time annual figure), never the undergrad sticker copied down, never
a guessed count:

- Eastman graduate degrees at Eastman's published full-time annual tuition — $49,148 academic
  (MA Musicology / Music Theory / Ethnomusicology / Music Leadership) and $53,616 performance
  with weekly applied lessons (Master of Music, D.M.A.), per-unit $2,234 (2026-27).
- Warner School master's + EdD annualized from Warner's published $1,860/credit-hour rate ×
  each program's published credits (master's 30, Higher Ed 36, Counseling 60, EdD 90; 2026-27).
- School of Nursing master's + DNP annualized from Nursing's published $1,740/credit-hour rate ×
  each program's published credits (CNL 35, Nursing Education 37, Leadership 31, NP 47, Direct
  Entry 70, DNP 39, DNP Nurse Anesthesia 103; 2026-27).
- Simon MS Marketing Analytics + MS AI in Business keep their published $68,000 full-time rate.

After this, master's coverage is 51/52 and professional 6/7 — the only remaining graduate nulls
are genuine honest omissions: the part-time Professional MBA (per-credit, no verified program
total), the DBA (part-time employer-sponsored, no published annual), and the Eastman/Warner PhDs
whose funding is not guaranteed (each recorded in ``_standard.omitted`` with a reason).

Deploy-safety mirrors ``rochreapply1``: the idempotent ``rochester_profile.apply()`` runs inside a
``lock_timeout``-bounded SAVEPOINT and is skipped (not hung) if it cannot grab locks quickly,
still recording as applied so the chain advances. ``backfill_program_preferences`` is called after
apply so every program keeps a derived target-applicant row (idempotent; claimed rows untouched).
The routine re-verifies the tuition coverage LIVE after deploy.

Revision ID: rochtuition2
Revises: rochreapply1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rochester_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "rochtuition2"
down_revision = "rochreapply1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            applied = rochester_profile.apply(session)
            print(f"  rochtuition2: rochester_profile.apply -> {applied}")
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == rochester_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  rochtuition2: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
