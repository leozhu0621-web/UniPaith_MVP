"""enrich Dartmouth College profile (data-only, no DDL)

Takes Dartmouth's institution-level seed to gold (rankings, report-card, admissions
funnel, diversity, scale, outcomes, cost/aid, research + campus-life resources, verified
news feed) and replaces its 5 empty stub programs with a real, verified, field-specific
catalog of 43 programs across all five degree-granting schools, plus derived
program-preference rows for the program -> student match — via
``unipaith.data.dartmouth_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Dartmouth College is absent.

Revision ID: dartprof1
Revises: ufprof1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import dartmouth_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dartprof1"
down_revision = "ufprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    if dartmouth_profile.apply(session):
        inst = session.scalar(
            select(Institution).where(
                Institution.name == dartmouth_profile.INSTITUTION_NAME
            )
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
