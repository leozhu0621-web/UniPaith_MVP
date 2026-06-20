"""enrich Emory University profile (data-only, no DDL)

Takes Emory's institution-level seed to gold (rankings, report-card, admissions funnel,
diversity, scale, outcomes, cost/aid, research + campus-life resources, verified Trumba
events feed + 4-photo gallery) and replaces its 5 empty stub programs with a real,
verified, field-specific catalog of 46 programs across nine schools, plus derived
program-preference rows for the program -> student match — via
``unipaith.data.emory_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Emory University is absent.

Revision ID: emoryprof1
Revises: dartpromptmerge1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import emory_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "emoryprof1"
down_revision = "dartpromptmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    if emory_profile.apply(session):
        inst = session.scalar(
            select(Institution).where(Institution.name == emory_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
