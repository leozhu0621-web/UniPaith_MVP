"""Boston College — review-sourcing + undergrad tuition-year fixes (PR #1257 follow-up)

Addresses independent review feedback on the merged BC enrichment:
- external_reviews must carry INDEPENDENT sourcing (manifest authoritative_2x), so the two
  reviews whose source list was first-party-only (``bc-msa``, ``bc-economics-phd`` — a lone
  ranking with no independent qualitative coverage) are dropped to an honest omission, and
  the kept reviews (MSW, J.D., MSN, DNP) gain their independent U.S. News source explicitly.
- The undergraduate ``cost_data.year`` is corrected back to "2024-25" to match the shipped
  $70,702 scalar (BC's 2025-26 undergraduate rate is higher, so a "2025-26" label misstated
  the value).

Idempotent re-apply of ``boston_college_profile.apply()`` + ``backfill_program_preferences``.

Head-sync: chains off ``bcgradtuition1`` (the merged BC head) so this PR carries one head.
Deploy-safety: fleet SAVEPOINT + lock_timeout skip pattern; the routine re-verifies live.

Revision ID: bcreviewfix1
Revises: bcgradtuition1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import boston_college_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bcreviewfix1"
down_revision = "bcgradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            boston_college_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == boston_college_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  bcreviewfix1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
