"""enrich Brown University profile (data-only, no DDL)

Takes Brown's institution-level seed to gold (rankings, report-card, admissions funnel,
diversity, scale, outcomes, cost/aid, research + campus-life resources with links, a
verified 5-photo campus gallery, and working Brown News + LiveWhale events feeds) and
replaces its 5 empty stub programs with a real, verified, field-specific catalog of 57
programs across Brown's seven degree-granting schools, plus derived program-preference
rows for the program -> student match — via ``unipaith.data.brown_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Brown University is absent.

Revision ID: brownprof1
Revises: gatechproftuition1
Create Date: 2026-06-24
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import brown_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "brownprof1"
down_revision = "gatechproftuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    if brown_profile.apply(session):
        inst = session.scalar(
            select(Institution).where(
                Institution.name == brown_profile.INSTITUTION_NAME
            )
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
