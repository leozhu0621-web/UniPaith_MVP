"""persist cip_code on every Princeton program (matcher field/interest signal)

Princeton's ``_apply_programs`` never wrote ``Program.cip_code``, so every Princeton
program stored a NULL CIP — leaving the CPEF matcher blind on the field/interest
signal for the whole catalog (the core-match-input rule: every program MUST carry a
real ``cip_code``). This re-applies ``princeton_profile.apply()`` after adding
``p.cip_code = spec.get("cip")`` (mirroring caltech/chicago), so each program now
carries its verified CIP join key to ``ref_majors`` and the matcher vocabulary.

Data-only; idempotent; no DDL.

Revision ID: princetonprof10
Revises: cmuprof6
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof10"
down_revision = "cmuprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    princeton_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass
