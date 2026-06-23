"""Berkeley published professional-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the professional-tier tuition STARVATION the catalog aggregate hid:
Berkeley's bachelor's tier shipped 100% but the professional tier was 0/20 (all null).
Berkeley publishes professional tuition on the Office of the Registrar fee schedule
(PDST programs) and the SSGPDP page (self-supporting LL.M. and MFE), so the nulls
were skipped knowable fields, not honest omissions.

Rates are school-distinct and none equal the $16,347 undergraduate sticker.

Idempotent: re-applies ``berkeley_profile.apply()`` and re-derives program-preference
rows.

Revision ID: berkeleygradtuition1
Revises: dukegradtuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleygradtuition1"
down_revision = "dukegradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    berkeley_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == berkeley_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
