"""Harvard un-enumerated CIP-title residual → drop spurious certificate (REPAIR_BACKLOG #1)

The run-77 CIP-title repair (``harvardcipnames1``) resolved exactly the five
backlog-enumerated federal CIP taxonomy titles but left a sixth same-class title live —
the "…and Related Sciences" suffix form (no comma before "and"), which the build's
``_ROLLUP_NAME_RE`` did not yet catch:

  * "Physiology, Pathology and Related Sciences" (CIP 26.09, certificate) — DROPPED.
    Harvard does not confer a standalone FAS graduate certificate under this federal CIP
    title; human physiology and pathobiology live in MCB/OEB research and HMS graduate
    courses (HBTM), not a named FAS certificate.

``_ROLLUP_NAME_RE`` is tightened so any future un-resolved "…and Related Sciences/Services"
suffix title raises the build gate (miss #2 whole-class rule). A whole-catalog re-scan with
the miss-#2 CIP-title tells now returns ZERO across all Harvard program names.

Re-applies ``harvard_profile.apply()`` and re-derives the matcher's target-applicant rows.

Revision ID: harvardcip2
Revises: cornellcip2
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardcip2"
down_revision = "cornellcip2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    harvard_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == harvard_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
