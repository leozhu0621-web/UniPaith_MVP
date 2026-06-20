"""Purdue re-apply clean descriptions — force the de-fabricated catalog live

The ``purduedefab1`` revision (#832) regenerated every Purdue program description from a
verified, field-specific discipline definition + Purdue's real owning college (removing the
peer-institution copy — JHU's Chesapeake/Writing Seminars, Penn's Wharton/Perelman, Cornell's
CALS, Northwestern's McCormick — and the 82% verbatim-across-levels stamping). But the live
API still served the OLD peer-contaminated descriptions: ``purduedefab1`` was stamped into
``alembic_version`` during the dual-head deploy failure (it raced the scholarships migration —
fixed by ``purduescholmerge1``), so Alembic never re-ran its ``apply()`` and the clean data
never reached production (REPAIR_BACKLOG run 61 critical #1: 31 peer rows + 82% verbatim still
live).

This is a FRESH revision, so ``alembic upgrade head`` runs it unconditionally and
``purdue_profile.apply()`` overwrites every stale description with the clean per-credential
text. This run also dropped the 3 "Area Studies" CIP-rollup rows (no verified single Purdue
degree by that title), so ``apply()`` deletes those slugs. ``backfill_program_preferences``
then re-derives the target-applicant rows for the refreshed catalog (skipping claimed rows).

Revision ID: purduereapply1
Revises: purduescholmerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile
from unipaith.models.institution import Institution

revision = "purduereapply1"
down_revision = "purduescholmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    purdue_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == purdue_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        from unipaith.services.match.derive_preferences import (
            backfill_program_preferences,
        )

        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
