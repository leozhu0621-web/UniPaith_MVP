"""enrich UF: working LiveWhale feeds + program_preferences backfill

Re-applies ``uf_profile`` after switching ``content_sources`` to the verified
LiveWhale events RSS (``www.ufl.edu/feed/`` is an empty channel) and backfills
grounded ``program_preferences`` rows for the matcher.

Revision ID: ufprof2
Revises: ufprof1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ufprof2"
down_revision = "ufprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uf_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uf_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
