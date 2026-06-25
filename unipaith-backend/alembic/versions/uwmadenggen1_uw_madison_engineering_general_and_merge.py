"""UW-Madison — resolve federal CIP-rollup "Engineering, General" name + merge dual head.

Two jobs in one migration:

1. **Data (REPAIR_BACKLOG #1, whole-class completion):** the prior UW-Madison repair
   (``uwmadareastudies1``) cleared the "Area Studies" CIP rollup but LEFT the sibling
   federal CIP 14.01 "Engineering, General" rollup (rendered "Master of Science in
   General Engineering" + "Graduate Certificate in General Engineering" — generic degrees
   UW-Madison does not confer, carrying fabricated descriptions). Per miss #2 ("clear the
   WHOLE class, re-scan, get ZERO") this re-applies ``uw_madison_profile.apply()`` with:
     - CIP 14.01 masters → the real College-wide **Master of Engineering** (MEng),
       administered through Interdisciplinary Professional Programs, named options in
       Engineering Data Analytics, Polymer Engineering, and Sustainable Systems Engineering.
     - the generic CIP 14.01 certificate row is DROPPED (no single generic engineering
       graduate certificate exists; apply() reconciles the removed slug).
   Source: guide.wisc.edu/graduate/engineering-college-wide/engineering-meng/. The whole
   catalog re-scans to ZERO miss-#2 rollup tells; apply() is idempotent and its slug
   reconciliation also drops any stale duplicate-render rows (REPAIR_BACKLOG #2). Re-derives
   target-applicant rows.

2. **Merge dual head:** the two REPAIR_BACKLOG #1 "Area Studies" repairs (U-Chicago
   ``chicagoareastudies1`` #1127 and UW-Madison ``uwmadareastudies1`` #1129) each branched
   off ``berkvandmerge1`` and auto-merged, leaving ``origin/main`` with two heads — so
   Deploy Backend's ``alembic upgrade head`` failed and the stranded UW-Madison Area Studies
   fix never reached production. This migration's two-parent ``down_revision`` unifies them
   into a single head, so applying it first runs the stranded ``uwmadareastudies1`` (Area
   Studies → LACIS / African Studies) and then this row (Engineering, General → MEng).

Revision ID: uwmadenggen1
Revises: chicagoareastudies1, uwmadareastudies1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwmadenggen1"
# Re-pointed onto uwmadchicagomerge1 (#1130) after that pure merge-only migration landed on
# main and unified the chicagoareastudies1 + uwmadareastudies1 dual head first. This migration
# is now a normal linear data migration on top of it (the "merge dual head" job below was done
# by #1130), carrying only the "Engineering, General" -> Master of Engineering data fix.
down_revision = "uwmadchicagomerge1"
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
