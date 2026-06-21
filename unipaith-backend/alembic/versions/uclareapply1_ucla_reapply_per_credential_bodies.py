"""UCLA re-apply per-credential bodies — force the clean catalog live

``uclapercrd1`` (#975) regenerated every UCLA program description with sibling-aware
``_assign_descriptions`` (67 frame-stripped shared-body fields → 0 in repo). The live
API still serves 192 stale "UCLA's Master of…" / "UCLA's doctoral program…" frame
bodies on 67 multi-credential fields — ``uclapercrd1`` was stamped during the dual-head
deploy-cancel race before ``apply()`` reached production (same class of failure as
``purduereapply1`` / Michigan #953 / Columbia #942).

This is a FRESH revision so ``alembic upgrade head`` runs it unconditionally and
``ucla_profile.apply()`` overwrites every stale description with the clean per-credential
text already in the data module. ``backfill_program_preferences`` then re-derives target-
applicant rows (skipping claimed rows).

Revision ID: uclareapply1
Revises: deepintelfix1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclareapply1"
down_revision = "deepintelfix1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucla_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
