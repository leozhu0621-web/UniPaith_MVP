"""UCLA published professional-tier tuition backfill (REPAIR_BACKLOG #4)

Clears the professional-tier tuition STARVATION the catalog aggregate hid:
UCLA's bachelor's tier shipped 100% and master's tier is largely filled, but the
professional tier was 0/4 (all null). UCLA publishes distinct registration fees for
its J.D., M.D., D.D.S., and D.N.P. programs on each school's tuition page, so the
nulls were skipped knowable fields, not honest omissions.

Rates are school-distinct and none equal the $15,202 undergraduate sticker.

Idempotent: re-applies ``ucla_profile.apply()`` and re-derives program-preference
rows.

Revision ID: uclagradtuition1
Revises: berkeleygradtuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclagradtuition1"
down_revision = "berkeleygradtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ucla_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == ucla_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
