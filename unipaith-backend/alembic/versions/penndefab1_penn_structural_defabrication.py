"""Penn — structural de-fabrication: real degree names + per-credential descriptions.

Re-applies ``penn_profile.apply()`` after the penndefab1 data-module repair (SKILL miss
#2/#8): the Scorecard CIP-rollup catalog shipped 58 federal-taxonomy program names with
the rollup echoed into ``department``, 28 literal ``(CIP NN.NN)`` codes, and one
description per field stamped verbatim across every credential level. The module now
resolves each rollup to Penn's REAL published degree (or DROPS the federal aggregation
buckets with no single named degree — the catalog legitimately shrinks 250 → 192), sets
``department`` to the real owning Penn school, and frames each credential level's verified
fact distinctly. The reconciliation in ``_apply_programs`` deletes/unpublishes the dropped
rollup rows. anti_stub.analyze clean + 0 rollup/CIP/field-echo.

Also derives ``program_preferences`` for every Penn program (skips claimed rows) so the
program -> student match direction fires.

Revision ID: penndefab1
Revises: cornellpeer1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "penndefab1"
down_revision = "cornellpeer1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    penn_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == penn_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
