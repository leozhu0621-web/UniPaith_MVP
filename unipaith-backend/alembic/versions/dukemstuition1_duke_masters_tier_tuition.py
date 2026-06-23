"""Duke published master's-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the master's-tier tuition STARVATION the catalog aggregate hid:
Duke's bachelor's tier shipped 100% and the professional tier is filled, but
17 master's rows were still null (21/38). Each school publishes tuition on its
official page, so the nulls were skipped knowable fields, not honest omissions.

Rates verified from Fuqua / Pratt / Graduate School / School of Medicine /
School of Nursing / School of Law bulletins and program pages — none equal the
$70,265 undergraduate sticker. PhD rows remain funded-omit-with-reason.

Idempotent: re-applies ``duke_profile.apply()`` and re-derives program-preference
rows.

Revision ID: dukemstuition1
Revises: uclagradtuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dukemstuition1"
down_revision = "uclagradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    duke_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == duke_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
