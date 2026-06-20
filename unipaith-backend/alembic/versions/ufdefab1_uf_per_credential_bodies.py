"""UF per-credential bodies + college/department mismatch fixes (REPAIR BACKLOG HIGH #4)

The prior UF composition stamped one shared discipline definition plus a shared
"engages this discipline at the {level} level" classification clause across every
credential level of a field, so 102 multi-credential fields shared a body once the
level frame was stripped (anti_stub.frame_stripped_shared_body — miss #8 credential
frame). This migration re-applies ``uf_profile.apply()`` with a distinct
per-(field, degree_type) body for every credential level (what THAT degree studies at
THAT level — ``_level_body``); gold MIT = 0 frame-stripped shared body, now enforced
by the catalog build gate and ``test_anti_stub_gate``. It also corrects nine
college/department mismatches (Health Sciences / Allied Health → PHHP; Nutrition
Science / Human Development & Family Studies / Apparel Design / Agriculture → CALS;
Liberal Arts → CLAS; Bioinformatics → Engineering) so each description's named college
matches the program's department. Idempotent (``replace=True``); re-derives
target-applicant rows for the matcher.

Revision ID: ufdefab1
Revises: ricepercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uf_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ufdefab1"
down_revision = "ricepercred1"
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
