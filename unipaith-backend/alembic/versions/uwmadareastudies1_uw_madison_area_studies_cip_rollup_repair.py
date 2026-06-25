"""UW-Madison — resolve the federal CIP-rollup "Area Studies"/"Engineering, General" names.

Also a MERGE migration: it unifies the dual alembic head left on ``main`` by the
concurrent ``berkeleyareastudies1`` (Berkeley repair) and ``vanderbiltprof1`` merges
(both branched off ``brownprof1``), so ``alembic upgrade head`` is single-headed again and
the stranded Berkeley repair deploys alongside this one.

Re-applies ``uw_madison_profile.apply()`` after the REPAIR_BACKLOG #1 fix:
  * CIP 05.01 "Area Studies" → UW-Madison's real published area-studies degrees
    (Institute for Regional and International Studies):
      - B.A.  → Latin American, Caribbean, and Iberian Studies (LACIS)
      - cert  → Graduate Certificate in African Studies (African Studies Program)
      - M.A.  → Latin American, Caribbean, and Iberian Studies (LACIS)
  * CIP 14.01 "Engineering, General" → the real College-wide Master of Engineering
    (Engineering, MEng); the federal-bucket certificate row (no single generic
    engineering graduate certificate — InterPro capstone certificates are named) is
    dropped.
``apply()`` is idempotent and reconciles the dropped certificate slug
(delete-if-unreferenced, else unpublish). Derives ``program_preferences`` for every
UW-Madison program (skips claimed/first-party rows).

Sources verified: guide.wisc.edu LACIS BA/MA, African Studies graduate certificate, and
Engineering, MEng pages.

Revision ID: uwmadareastudies1
Revises: berkeleyareastudies1, vanderbiltprof1
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
down_revision = ("berkeleyareastudies1", "vanderbiltprof1")
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
