"""UVA — re-apply uva_profile after review-feedback fixes (degree_type / delivery / requirements)

Follow-up to ``uvaprof1`` addressing the Codex review on PR #1174 (all verified):
- Doctor of Nursing Practice ``degree_type`` ``phd`` → ``professional`` (a practice
  doctorate belongs with JD/MD, not the research-PhD bucket, for degree-type filters).
- M.S. in Data Science keeps the residential row and adds the verified online /
  part-time delivery row; M.S. in Business Analytics stays on-campus and is marked
  part-time available.
- The LL.M. now takes graduate-law admissions requirements instead of the J.D.'s
  LSAT/CAS checklist.

The data fix lives in ``uva_profile`` (``apply()`` is idempotent); this migration just
re-runs it so the changed rows update in place. No structural schema change.

Deploy-safety (washuprof1/uvaprof1 pattern): the idempotent data apply runs inside a
SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if
it cannot get its locks quickly. The migration still records as applied so the chain
advances; ``uva_profile.apply()`` is idempotent and the routine re-applies it.

Revision ID: uvarev1
Revises: purduefeedimg1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uva_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uvarev1"
down_revision = "purduefeedimg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            uva_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == uva_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                # Drop this institution's DERIVED preference rows so backfill RE-DERIVES
                # them from the now-corrected degree_type (DNP phd → professional changes
                # pref_levels) — backfill_program_preferences skips rows that already exist,
                # so without this delete the live DNP/LL.M. signals would stay stale.
                # Claimed / first-party rows are NEVER touched.
                prog_ids = session.scalars(
                    select(Program.id).where(Program.institution_id == inst.id)
                ).all()
                if prog_ids:
                    session.execute(
                        delete(ProgramPreference).where(
                            ProgramPreference.program_id.in_(prog_ids),
                            ProgramPreference.source == "derived",
                        )
                    )
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(f"  uvarev1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
