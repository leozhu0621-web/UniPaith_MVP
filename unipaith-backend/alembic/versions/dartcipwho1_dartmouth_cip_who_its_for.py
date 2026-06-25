"""Dartmouth matcher-core cip_code + universal-depth who_its_for backfill

Clears two live gaps the editorially-complete catalog masked (REPAIR_BACKLOG run 84):

  * #1 — cip_code STARVATION: all 43 Dartmouth programs shipped ``cip_code = null``, so
    the CPEF matcher scored every program field-blind on the CIP join key to ref_majors
    + the field-66 vocabulary. ``dartmouth_profile._CIP_BY_FIELD`` now stamps the NCES
    CIP-2020 4-digit series (``NN.NN`` family — the live convention) on every row; the
    build fails if any program lacks one. A taxonomy stamp, never a guess.

  * #4 — who_its_for 0%: the universal-depth "Who it's for" field was null on all 43
    programs. ``dartmouth_profile._WHO_BY_SLUG`` now carries a field-specific 1-2 sentence
    audience statement for every program (gold-contrast, never a "{field}" stub).

Reviews stay coverage-gated: the Tuck MBA carries real third-party coverage; the rest
remain honestly omit-with-reason (no fabrication).

Idempotent: re-applies ``dartmouth_profile.apply()`` and re-derives program-preference
rows so the program -> student match direction stays covered.

Revision ID: dartcipwho1
Revises: berkeleycip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import dartmouth_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dartcipwho1"
down_revision = "berkeleycip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    dartmouth_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == dartmouth_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
