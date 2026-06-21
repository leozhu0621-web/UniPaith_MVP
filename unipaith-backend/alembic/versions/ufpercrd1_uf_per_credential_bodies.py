"""University of Florida per-credential description repair (REPAIR BACKLOG HIGH #5).

``_uf_description`` prepended the SAME ~180-char discipline definition to every credential
level of a field, so a field's BA/MS/PhD siblings shared that leading sentence verbatim —
the run-65 dilution evasion that reads 0 on the fraction-only default but 54 fields under
the absolute-150 floor (``frame_stripped_shared_body(..., abs_chars=150)``). The build now
keeps ONE anchor row per field carrying the discipline definition and gives every other
credential sibling its own distinct, level-specific body that leads with the field's topic
(taken verbatim from the definition, so it stays distinct across fields) — no sibling pair
shares a >=150-char run (gold MIT = 0). Re-applies ``uf_profile.apply()`` and re-derives
program-preference rows.

Revision ID: ufpercrd1
Revises: berkeleypercrd1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ufpercrd1"
down_revision = "berkeleypercrd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uf_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uf_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
