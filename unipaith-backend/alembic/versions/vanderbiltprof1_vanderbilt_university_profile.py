"""enrich Vanderbilt University profile (data-only, no DDL)

Takes Vanderbilt's institution-level seed to gold (rankings, report-card stats, cost of
attendance, research + campus-life resources with links, a verified 5-photo campus gallery,
and working Vanderbilt News RSS + LiveWhale events feeds) and replaces its 5 empty stub
programs with a real, verified, field-specific catalog of 107 programs across Vanderbilt's
eleven degree-granting schools and colleges, plus derived program-preference rows for the
program -> student match — via ``unipaith.data.vanderbilt_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Vanderbilt University is absent.

Revision ID: vanderbiltprof1
Revises: brownprof1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import vanderbilt_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "vanderbiltprof1"
down_revision = "brownprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    if vanderbilt_profile.apply(session):
        inst = session.scalar(
            select(Institution).where(
                Institution.name == vanderbilt_profile.INSTITUTION_NAME
            )
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
