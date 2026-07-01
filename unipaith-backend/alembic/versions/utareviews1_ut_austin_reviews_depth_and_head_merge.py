"""UT Austin external_reviews depth pass (REPAIR_BACKLOG #5) + dual-head merge.

Adds hand-gathered, program-specific ``external_reviews`` to eight additional coverable
UT Austin flagship programs (MS Finance; the online MS Data Science; the graduate MS
Computer Science; the top-five undergraduate Aerospace, Chemical, and Civil Engineering
majors; the professional Master of Architecture; and the Government / political-science
B.A.). Each review is summarized and cited from real third-party coverage (official
McCombs employment reports, U.S. News / Financial Times / DesignIntelligence rankings,
edX/independent student reviews) — no synthesized-from-metadata reviews. The Pharm.D.
annual tuition scalar stays honestly omitted (UT publishes it only via a login-gated
calculator/PDF; the sole concordant figure is an IPEDS-republisher echo, failing the
two-independent-source gate).

Chains onto ``dartbcmerge1`` (the merge migration #1260 that unified the concurrent
``bcreviewfix1`` + ``dartreviews1`` auto-merge dual head) — the single current head.

Idempotent: re-applies ``ut_austin_profile.apply()`` (replace/dedup) and re-derives the
grounded ``program_preferences`` rows. No programs are added.

Revision ID: utareviews1
Revises: dartbcmerge1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utareviews1"
down_revision = "dartbcmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    session.flush()
    inst = session.scalar(
        select(Institution).where(Institution.name == ut_austin_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
