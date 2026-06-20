"""Repair the UIUC catalogue's CRITICAL #1 defects (grader run 67): ~30 rows shipped raw
scraped catalogue debris (truncated fragments, degree-requirement / course-code lists,
department contact blocks) and 14 fields shared one researched body across their BA/MS/PhD
behind a credential frame. Each affected row is replaced with researched, per-credential,
field-specific prose grounded in UIUC's official academic catalog / department pages
(real owning college, what THAT credential studies; gold MIT shares 0%). Re-applies the
profile in place (slug-matched) and re-derives program-preference rows.

Revision ID: uiucprof5
Revises: uwmadpercred2
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uiucprof5"
down_revision = "uwmadpercred2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uiuc_profile.apply(session)
    session.flush()
    inst = session.scalar(
        select(Institution).where(Institution.name == uiuc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
