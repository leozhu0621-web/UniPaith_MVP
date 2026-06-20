"""rebuild Northwestern catalog to real programs (data-only, no DDL)

Replaces the prior 306-row IPEDS×award-level mint — whose FIELD-keyed shared description
bodies were pervasively cross-institution-contaminated (Wharton / Cornell / Berkeley /
Weill Cornell / Johns Hopkins signatures find-replaced onto Northwestern rows) and which
minted programs Northwestern does not offer (agriculture, dental medicine, veterinary) —
with an EXPLICIT, researched catalog of Northwestern's REAL degree programs. Every program
carries a real name, real owning department, and a per-credential field-specific
description grounded only in verified Northwestern units (REPAIR BACKLOG #1
cross-institution contamination + #6 frame+tail-share). Derives program-preference rows
for the program -> student match — via ``unipaith.data.northwestern_profile.apply()``.

No schema (DDL) changes. Idempotent; no-op when Northwestern University is absent. Programs
no longer in the canonical catalog are unpublished (if referenced) or deleted.

Revision ID: nwrebuild1
Revises: emoryprof1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nwrebuild1"
down_revision = "emoryprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    if northwestern_profile.apply(session):
        inst = session.scalar(
            select(Institution).where(Institution.name == northwestern_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
