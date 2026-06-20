"""rebuild Purdue catalog to real programs (data-only, no DDL)

Replaces the prior IPEDS×award-level generated catalog whose per-credential descriptions
were a generic encyclopedia field DEFINITION shared verbatim across a field's credential
siblings behind a per-credential frame ("Graduate study. " / "Doctoral research. ") — the
run-65 credential-FRAME + tail-shared-body evasion (REPAIR BACKLOG #2, miss #8): the
leading-prefix anti-stub metric reads 0 while every BA/MS/PhD of one field shares the same
definition. Replaces it with an EXPLICIT, researched catalog of Purdue's 172 REAL degree
programs across all 10 colleges, each with a per-program, field-specific description
grounded only in verified Purdue units (no generic definition, no shared body, no
classification frame, zero peer signatures). Drops the 95 CIP×award-level certificate mints
and ~16 CIP-rollup / duplicate degree rows. Derives program-preference rows for the
program -> student match — via ``unipaith.data.purdue_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Purdue is absent. Programs no longer in the
canonical catalog are unpublished (if referenced) or deleted.

Revision ID: purduerebuild1
Revises: nwrebuild1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "purduerebuild1"
down_revision = "nwrebuild1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    if purdue_profile.apply(session):
        inst = session.scalar(
            select(Institution).where(Institution.name == purdue_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
