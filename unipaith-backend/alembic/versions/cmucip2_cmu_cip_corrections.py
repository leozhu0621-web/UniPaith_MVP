"""Carnegie Mellon CIP corrections (PR #1198 review follow-up).

Re-applies ``carnegie_mellon_profile.apply()`` after correcting two ``cip_code`` mappings
that resolved to the wrong field in the repo's own CIP vocabulary
(``data/reference/ref_majors.jsonl``), flagged in the #1198 review:

  * Human Computer Interaction (B.S. / M.HCI / Ph.D.) was ``11.0104`` (Informatics) — the
    repo carries a DEDICATED HCI code ``30.3101`` ("Human Computer Interaction"). With the
    old value the CPEF field signal fell through CIP family 11 and scored HCI as computer
    science; ``30.3101`` resolves the HCI/design/behavioral-science field correctly.
  * MS in Regenerative & Sustainable Design was ``04.0501``, which ``ref_majors`` defines as
    "Interior Architecture"; the correct match is ``04.0403`` ("Sustainable Design/
    Architecture").

The Learning-Engineering and Societal-Computing rows keep ``11.0104`` (Informatics) — they
are genuinely informatics programs, not HCI. As with the parent migration, the corrected
CIP must reach the program -> student field signal, so this deletes the unclaimed
``source="derived"`` ProgramPreference rows for CMU and re-derives them. Direct apply (no
lock-bounded skip); verify-live on content.

Revision ID: cmucip2
Revises: cmucipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cmucip2"
down_revision = "cmucipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    carnegie_mellon_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == carnegie_mellon_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        prog_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if prog_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(prog_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
        # The corrected CIP changes the program-side field signal, so any cached
        # MatchResult for these programs is stale. Mark them stale (the same
        # invalidation institution_service.update_program() does) so GET /me/matches
        # lazily rescores against the corrected data instead of serving old scores.
        if prog_ids:
            session.execute(
                MatchResult.__table__.update()
                .where(MatchResult.program_id.in_(prog_ids))
                .values(is_stale=True)
            )
    session.flush()


def downgrade() -> None:
    pass
