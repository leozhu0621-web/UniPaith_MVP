"""Berkeley truncated CIP-rollup program-name repair (follow-up to berkeleytpl2 / #1026).

#1026 cleared the template-slot grammar and backfilled graduate tuition but left five
fields' program NAMES truncated to the first comma of their CIP rollup ("Doctor of
Philosophy in Ethnic", "…in Slavic", "…in Linguistic", "…in Electrical") — and its
sibling descriptions embed that truncated designation verbatim. This re-applies
``berkeley_profile.apply()`` so the real Berkeley degree names ("…in Ethnic Studies",
"…in Slavic Languages and Literatures", "…in Linguistics", "…in Electrical Engineering",
"…in East Asian Languages and Cultures") and the corrected descriptions persist.
Re-derives program-preference rows (idempotent).

Revision ID: berkeleynames1
Revises: berkeleytpl2
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleynames1"
down_revision = "berkeleytpl2"
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
