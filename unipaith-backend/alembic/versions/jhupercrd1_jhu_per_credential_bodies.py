"""JHU per-credential description repair (REPAIR BACKLOG HIGH #11).

Three fields carried a verified field clause long enough (~150 chars) that, stamped
verbatim across their credential siblings, the shared clause alone tripped the
absolute-150 frame-stripped shared-body floor (miss #8 fraction-floor): Anthropology
(BA / certificate / MS), Chemical Engineering (BS / certificate / MS), and
Communication Studies (certificate / MS). Each row now carries a per-slug researched,
credential-distinct body (``SLUG_DESCRIPTIONS``) so no two siblings of a field share a
>= 150-char run (frame_stripped_shared_body abs150 = 0; gold MIT = 0). Re-applies
``jhu_profile.apply()`` and re-derives program-preference rows.

Revision ID: jhupercrd1
Revises: uclapercrd1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "jhupercrd1"
down_revision = "uclapercrd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    jhu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == jhu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
