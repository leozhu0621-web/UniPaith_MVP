"""UW-Madison distinct per-credential bodies — clear absolute shared-field-body

The ``uwmadpercred1`` pass stamped one verified FIELD_DESCRIPTIONS clause across every
credential sibling and appended a generic per-level tail, so the leading field clause was
still shared verbatim across BA/Cert/MS/PhD — invisible to the frame-stripped metric (which
over-strips a leading clause) and the leading-prefix metric (which misses a shared tail),
but a real credential-frame + one-shared-field-body defect (110/110 multi-credential fields
share a >=80-char body; gold MIT = 0). This migration re-applies
``uw_madison_profile.apply()`` with sibling-aware descriptions: each field's bachelors (else
its lowest credential) keeps the full verified clause, and every other credential carries a
distinct level frame + the field's real-subarea focus, so no two programs (same field OR
cross-field) share a >=80-char body. Idempotent; re-derives target-applicant rows.

Revision ID: uwmadpercred2
Revises: jhupercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwmadpercred2"
down_revision = "jhupercred1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uw_madison_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == uw_madison_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
