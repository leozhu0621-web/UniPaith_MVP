"""UW-Madison — resolve federal CIP-rollup "Area Studies" names (REPAIR BACKLOG #1)

Three rows shipped the federal CIP 05.01 series TITLE "Area Studies" verbatim as a
degree name (BA + Graduate Certificate + MS, dept "International Studies") — a degree no
institution confers under that literal name (miss #2 federal-CIP-rollup NAME class). This
migration re-applies ``uw_madison_profile.apply()`` with the three rows resolved to
UW-Madison's REAL published area-studies degrees + owning units:
  - Bachelor of Arts in Latin American, Caribbean, and Iberian Studies (IRIS)
  - Graduate Certificate in African Studies (African Studies Program)
  - Master of Arts in Latin American, Caribbean, and Iberian Studies (IRIS)
Sources: guide.wisc.edu (LACIS BA/MA, African Studies Graduate/Professional Certificate;
Institute for Regional and International Studies). Same slugs → in-place UPDATE; whole
catalog re-scanned to ZERO miss-#2 rollup tells. Idempotent; re-derives target-applicant
rows.

Revision ID: uwmadareastudies1
Revises: berkvandmerge1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwmadareastudies1"
down_revision = "berkvandmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uw_madison_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == uw_madison_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
