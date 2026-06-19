"""Cornell de-contamination — remove cross-institution peer units, de-roll-up CIP names.

Re-applies ``cornell_profile.apply()`` after CRITICAL #1 repair (REPAIR_BACKLOG;
SKILL miss #8 allowlist):
  * every cross-institution academic unit copied from a peer catalog (Penn, Berkeley,
    Johns Hopkins units; Penn Vet's New Bolton Center) replaced with Cornell's own
    verified unit or a true generic clause, allowlist-checked against Cornell's
    published org chart
  * remaining federal CIP-taxonomy titles resolved to Cornell's real degrees
    (Computational Biology, Linguistics, Ecology and Evolutionary Biology, Electrical
    and Computer Engineering, Human Development, Nutritional Sciences, History of
    Architecture and Urban Development) or dropped (Allied Health bucket)
Idempotent (replace=True). Derives ``program_preferences`` for every Cornell program.

Revision ID: cornelldecontam1
Revises: buprof13
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornelldecontam1"
down_revision = "buprof13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == cornell_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
