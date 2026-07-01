"""Boston College — fill graduate tuition tiers + external_reviews (matcher repair)

Re-applies ``boston_college_profile`` to clear the graduate-tuition matcher-starvation the
prior seed shipped: the master's (1/30) and professional (1/3) tiers were null, so the CPEF
budget signal ran blind on every graduate program. BC bills graduate tuition PER CREDIT, so
each master's/professional program now carries its verified published per-credit rate (2026-27,
by school) × published degree credits ÷ program years as the annual matcher scalar, cited per
program in ``cost_data`` — never the undergraduate sticker copied down. Only BC's Earth &
Environmental Sciences M.S. (no fixed credit total) keeps an honest ``cost_data`` omission.

Also attaches gathered→summarized→cited ``external_reviews`` (MBAn shape) to the coverable
programs (MBA, MS Finance, MS Accounting, MSW, J.D., MSN, DNP, Economics PhD), and corrects
the institution's U.S. News national rank to #36 (2026 edition, up one from #37 in 2025).

``boston_college_profile.apply()`` is idempotent (upsert by slug); this migration only updates
existing rows and re-derives ``program_preferences`` for any program lacking one.

Head-sync: chains off the current single head ``gtownreviews2`` so this PR carries exactly one
head (SKILL.md §8 head-sync).

Deploy-safety (fleet pattern): the data apply runs inside a SAVEPOINT bounded by
``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot get its locks
quickly; the migration still records as applied so the chain advances. The routine re-verifies
the live catalog (grad tuition coverage + reviews) after deploy and re-applies if skipped.

Revision ID: bcgradtuition1
Revises: gtownreviews2
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import boston_college_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bcgradtuition1"
down_revision = "gtownreviews2"
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
            f"  bcgradtuition1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
