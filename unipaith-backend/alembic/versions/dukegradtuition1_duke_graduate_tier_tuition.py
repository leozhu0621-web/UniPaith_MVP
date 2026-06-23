"""Duke published professional-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the professional-tier tuition STARVATION the catalog aggregate hid:
Duke's bachelor's tier shipped 100% but the professional tier was 2/9 (7 null).
Duke publishes professional tuition BY SCHOOL on each school's official 2025-26
tuition page, so the nulls were a skipped knowable field, not an honest omission.
Every figure is verified and stamped in ``duke_profile._COST_BY_SLUG``:

  * M.D. -> $72,297;
  * JD/LLM dual -> $93,450;
  * DPT -> $42,000;
  * OTD -> $43,000;
  * DNP -> $32,880 (avg semester × 2);
  * CRNA DNP -> $70,460.

Values are school-distinct and NONE equals the $70,265 undergraduate sticker.
PhD rows remain funded-omit-with-reason.

Idempotent: re-applies ``duke_profile.apply()`` and re-derives program-preference
rows.

Revision ID: dukegradtuition1
Revises: dartgradtuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dukegradtuition1"
down_revision = "dartgradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    duke_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == duke_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
