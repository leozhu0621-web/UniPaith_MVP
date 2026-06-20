"""enrich University of Notre Dame profile (data-only, no DDL)

Populates Notre Dame's canonical profile — rankings, school_outcomes, the seven
degree-granting colleges/schools, a verified 5-photo campus gallery, working
events feeds, a ~113-program real-named catalog with per-credential descriptions,
and external_reviews on flagship coverable programs — via
``unipaith.data.notre_dame_profile.apply()``, then backfills grounded
``program_preferences`` rows for the matcher.

No schema (DDL) changes. Idempotent; no-op when University of Notre Dame is absent.

Chained onto ``emoryprof1`` (the #885 head) so ``main`` keeps a single migration head.

Revision ID: ndprof1
Revises: emoryprof1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import notre_dame_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ndprof1"
down_revision = "emoryprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    notre_dame_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == notre_dame_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
