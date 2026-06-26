"""Johns Hopkins CIP corrections (PR #1200 review follow-up).

Re-applies ``jhu_profile.apply()`` after correcting five ``cip_code`` mappings flagged in
the #1200 Codex review — each now joins to the most exact entry in the repo's own CIP
vocabulary (``data/reference/ref_majors.jsonl``):

  * Learning Sciences:       13.0601 -> 13.0607 (Learning Sciences)
  * Engineering Design:      15.1501 -> 15.1502 (Engineering Design)
  * Rehabilitation Sciences: 51.2310 -> 51.2314 (Rehabilitation Science)
  * Ecology and Evolution:   26.1301 -> 26.1310 (Ecology and Evolutionary Biology)
  * Data Science:            30.7001 -> 11.0802 (Data Modeling/Warehousing/DB Admin)

The first four stay in their original 2-digit field family, so the matcher field signal is
unchanged — only the ref_majors join + derived-feature descriptions sharpen. Data Science
moves back to family 11 so the ``program_featurizer`` family-11 soft features (career arcs /
values / themes) fire instead of falling through unmapped family 30; the name "data science"
also aliases in ``field_canon``, so its field signal is preserved either way.

As with the parent migration, the changed CIP must reach the program -> student field signal,
so this re-derives the unclaimed ``source="derived"`` ProgramPreference rows and marks the
cached MatchResult rows for ALL JHU programs (claimed or not — apply() rewrites every row)
stale so GET /me/matches rescores. Direct apply (no lock-bounded skip); verify-live on content.

Revision ID: jhucip2
Revises: jhucipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "jhucip2"
down_revision = "jhucipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    jhu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == jhu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        all_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        if all_ids:
            # Drop every stale ``source="derived"`` row (regardless of claim status — a
            # claimed program can still carry a derived row if the school never edited
            # its preferences), but NEVER touch a first-party ``source="claimed"`` row.
            # backfill re-derives only the unclaimed ones; a claimed-but-derived program
            # is left with no row (neutral) rather than a row built on the old CIP.
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(all_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
        if all_ids:
            session.execute(
                MatchResult.__table__.update()
                .where(MatchResult.program_id.in_(all_ids))
                .values(is_stale=True)
            )
    session.flush()


def downgrade() -> None:
    pass
