"""Berkeley template-slot grammar repair + graduate tuition backfill (REPAIR BACKLOG CRITICAL C1).

Replaces slotted per-credential template bodies that doubled credentials and produced
machine-broken grammar ("Doctoral training in the Doctor of Philosophy in … research in of …")
with UF-style sibling-aware prose. Re-applies ``berkeley_profile.apply()`` and re-derives
program-preference rows.

Revision ID: berkeleytpl2
Revises: uftuitionmerge1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleytpl2"
down_revision = "uftuitionmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    berkeley_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == berkeley_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
