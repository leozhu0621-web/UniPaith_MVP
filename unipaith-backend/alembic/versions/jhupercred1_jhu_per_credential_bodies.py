"""Johns Hopkins per-credential bodies — frame-share repair

Re-applies ``jhu_profile.apply()`` after the data module was repaired:

- Replaces credential-frame + one shared field clause (81/82 multi-credential fields)
  with distinct per-credential ``_level_body`` text after each verified field clause
  (gold MIT = 0% ``frame_stripped_shared_body``).
- De-rolls residual "Area Studies" CIP bucket to Latin American, Caribbean, and
  Latinx Studies (REPAIR_BACKLOG HIGH #5).

Idempotent; re-derives target-applicant rows.

Revision ID: jhupercred1
Revises: jhumerge1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "jhupercred1"
down_revision = "jhumerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    jhu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == jhu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
