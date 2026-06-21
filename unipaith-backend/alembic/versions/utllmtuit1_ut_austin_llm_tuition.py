"""UT Austin LL.M. tuition correction (follow-up to utaustintuition1 / #1036).

#1036 backfilled UT Austin tuition but routed the LL.M. (a `masters` row) to the generic
graduate rate ($12,006) — a law degree billed at the School of Law's published annual rate
($33,304 resident / $49,490 non-resident, Texas Law 2026-27), understated by ~$21k. The
LL.M. now carries the verified law-school annual rate via `_MASTERS_TUITION_OVERRIDE`.

Idempotent: re-applies `ut_austin_profile.apply()` and re-derives program-preference rows.

Revision ID: utllmtuit1
Revises: utaustintuition1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utllmtuit1"
down_revision = "utaustintuition1"
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
