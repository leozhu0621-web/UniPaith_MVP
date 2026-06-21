"""Cornell terminate per-credential description bodies (REPAIR BACKLOG run 73 HIGH #3).

The cornellpercrd2 "sibling-aware per-credential bodies" repair cleared the frame-share
dimension but assigned anchor / slug bodies straight from ``_strip_cornell_frame`` (which
``.rstrip(".")``s to recover the bare field clause), so 115 of 237 Cornell descriptions
shipped UN-terminated and tripped the ``anti_stub.scrape_debris`` truncation tell live.
``_assign_descriptions`` now runs every assigned body through ``_terminate`` so each ends
in a sentence terminator (gold MIT = 0). Re-applies ``cornell_profile.apply()`` (which
overwrites ``description_text`` on every existing program) and re-derives the
program-preference rows.

Chained on ``michtuition1`` so this deploy also applies the Michigan tuition + IOE
doctoral repair (#1042) whose own Deploy Backend was cancelled in the auto-merge race.

Revision ID: cornelltrm1
Revises: michtuition1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornelltrm1"
down_revision = "michtuition1"
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
