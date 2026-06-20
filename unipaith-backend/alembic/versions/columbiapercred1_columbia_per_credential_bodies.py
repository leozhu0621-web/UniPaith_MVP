"""Columbia per-credential description repair (REPAIR BACKLOG HIGH #13).

Fourteen fields (Anthropology, Physics, Astronomy, Religion, Classics, French,
Operations Research, Applied Physics, Materials Science and Engineering, Chemical /
Civil / Computer / Earth-and-Environmental / Industrial Engineering) fell through to
the shared ``CORE`` fallback in ``columbia_field_descriptions``, so a field's BA / MS /
PhD rows carried ONE field clause behind a credential-keyed lead — 14 fields failed
the absolute-floor frame-stripped shared-body gate live (analyze read a false 0
because the credential frame relocated the shared body). Each of the 34 rows now
carries a ``SLUG_DESCRIPTIONS`` body researched per program from Columbia's own
bulletin / department pages and distinct across credential levels (gold MIT = 0%
frame-stripped shared body). Re-applies ``columbia_profile.apply()`` (idempotent,
slug-keyed) so the live catalog picks up the corrected descriptions, then re-derives
``program_preferences`` (skips claimed rows) so the program -> student match still fires.

Revision ID: columbiapercred1
Revises: utaustpercrd1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "columbiapercred1"
down_revision = "utaustpercrd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    columbia_profile.apply(session)
    session.flush()
    inst = session.scalar(
        select(Institution).where(Institution.name == columbia_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
