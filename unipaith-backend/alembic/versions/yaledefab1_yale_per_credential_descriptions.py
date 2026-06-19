"""Yale per-credential description de-fabrication

Removes the ``"{program_name}: "`` heading-doubling prefix from every generated
program description and gives each field's graduate rows their OWN doctoral/master's
clause (``GRADUATE_FIELD_DESCRIPTIONS``), so a field's credential siblings no longer
share a leading body (anti-stub verbatim / shared-leading-body / name_prefixed = 0,
gold-MIT baseline). Re-applies ``yale_profile.apply()`` (idempotent, replace-by-slug)
and re-derives target-applicant rows for the matcher.

Revision ID: yaledefab1
Revises: penndefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "yaledefab1"
down_revision = "penndefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    yale_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == yale_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
