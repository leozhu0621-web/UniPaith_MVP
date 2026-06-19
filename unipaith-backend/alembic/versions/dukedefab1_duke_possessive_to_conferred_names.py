"""Duke possessive-mint names → conferred degree designations (REPAIR BACKLOG #9)

Resolves Duke's 53 possessive-mint program names ("Bachelor's in {field}" /
"Master's in {field}") to the institution's conferred designations, the gold-MIT
naming form (SKILL miss #2 / REPAIR_BACKLOG run 64): the 50 Trinity College majors
become "Bachelor of Arts in {field}" (Trinity confers the A.B. across its majors;
the B.S. is the alternative in many science fields), and the 3 Pratt master's
("Master's in Biomedical / Electrical & Computer / Mechanical Engineering &
Materials Science") become "Master of Science in {field}" (Duke Graduate School
Bulletin). Descriptions were already certified-clean — names only. Re-applies
``duke_profile.apply()`` (idempotent, replace-by-slug, reconciles the 3 renamed
master's' old slugs) and re-derives target-applicant rows for the matcher.

Revision ID: dukedefab1
Revises: colyalemerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dukedefab1"
down_revision = "colyalemerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    duke_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == duke_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
