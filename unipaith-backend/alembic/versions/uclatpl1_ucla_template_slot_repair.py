"""UCLA template-slot grammar repair + tuition backfill (REPAIR_BACKLOG CRITICAL C2 + #7).

Replaces graduate sibling descriptions that slotted a raw fragment into a sentence frame and
produced machine-broken grammar ("...advances original dissertation research in of artistic
production..."; "...understanding of human.") with clean, verified per-credential topics, and
stamps the institution-published matcher-core ``tuition`` per credential level (undergraduate
sticker, academic graduate rate, funded $0 doctoral). Re-applies ``ucla_profile.apply()`` and
re-derives program-preference rows.

Revision ID: uclatpl1
Revises: stanfordtuit1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclatpl1"
down_revision = "stanfordtuit1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucla_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
