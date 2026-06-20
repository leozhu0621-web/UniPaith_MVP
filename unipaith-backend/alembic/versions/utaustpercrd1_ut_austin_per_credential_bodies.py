"""UT Austin per-credential description repair (REPAIR BACKLOG CRITICAL #2).

Replaces ``_finalize_descriptions`` (credential frame + ONE shared field body — 24
fields failed the frame-stripped shared-body gate live, plus 5 scrape-debris rows)
with sibling-aware ``_assign_descriptions`` so each credential level carries its
own researched body (gold MIT = 0%). Re-applies ``ut_austin_profile.apply()`` and
re-derives program-preference rows.

Revision ID: utaustpercrd1
Revises: nyuprof5
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utaustpercrd1"
down_revision = "nyuprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    session.flush()
    inst = session.scalar(
        select(Institution).where(Institution.name == ut_austin_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
