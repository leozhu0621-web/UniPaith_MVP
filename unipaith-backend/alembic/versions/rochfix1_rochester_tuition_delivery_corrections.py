"""University of Rochester — tuition / delivery-format / funding corrections (re-apply)

Follow-up to ``rochprof1`` addressing verified data-accuracy issues an automated PR review
flagged after that PR auto-merged. Re-applies the idempotent ``rochester_profile.apply()`` so
the corrected values reach the live rows:

- Undergraduate tuition scalar $67,080 (2024-25 Scorecard) → the current published
  $71,750 (2026-27, University of Rochester), so bachelor's budget-fit is not understated.
- M.D. tuition $75,690 → the official URMC cost-of-attendance $74,050 (2026-27).
- ``delivery_format = "on_campus"`` (a non-canonical value the schema does not accept) →
  ``in_person`` on the nine graduate rows that carried it, so delivery filters see them.
- Simon Executive MBA and part-time Professional MBA no longer priced at the full-time
  $60,000 (a copy-down across different billing bases) — they carry an honest cost omission;
  Simon MS in Marketing Analytics and MS in Artificial Intelligence in Business are now
  filled at their published $68,000/year (previously wrongly omitted).
- Eastman and Warner PhD rows no longer publish ``tuition=0`` / ``funded=True`` — their
  funding is partial-to-full and not guaranteed, so the scalar is omitted-with-reason
  (the A&S / Hajim / SMD / Simon research doctorates keep the verified full-funding $0).
- Master's Direct Entry to Nursing Practice duration 24 → 16 months (published pathway).
- Undergraduate application deadlines corrected to ED I (Nov 1) / ED II (Jan 5) / RD
  (Jan 5) — Rochester has no Early Action round.

Head-sync: chains off the current single head ``rochprof1`` so this PR carries exactly one
head. Deploy-safety: the idempotent data apply runs inside a ``lock_timeout``-bounded
SAVEPOINT and is SKIPPED (not hung) if it cannot grab locks quickly, still recording as
applied so the chain advances; the routine re-verifies the live values after deploy.

Revision ID: rochfix1
Revises: rochprof1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rochester_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "rochfix1"
down_revision = "rochprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            rochester_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == rochester_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  rochfix1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
