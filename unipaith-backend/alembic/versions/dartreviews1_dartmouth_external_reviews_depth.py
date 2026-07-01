"""Dartmouth external_reviews depth pass (REPAIR_BACKLOG #5)

Structure + descriptions + tuition are already gold on Dartmouth (the 3 null master's
are Guarini-FUNDED and honestly omitted-with-reason; PhDs funded-omit), so the
STRUCTURE-BEFORE-DEPTH gate is satisfied and the reviews depth pass runs on the now-real
catalog. Live sampling showed reviews on only 2 of 61 programs (the Tuck MBA + the Geisel
M.D.). This pass adds program-specific, third-party-sourced ``external_reviews`` (MBAn
shape) for eight more genuinely-coverable flagship programs:

  * Master of Engineering Management (MEM) — Thayer graduate-outcomes report;
  * Master of Engineering (MEng) — Thayer outcomes + U.S. News online engineering;
  * Master of Public Health (MPH / TDI) — U.S. News health schools;
  * Master of Arts in Liberal Studies (MALS) — LiberalArtsEdu top-ten list;
  * Bachelor of Arts in Economics — Niche / College Factual major rankings;
  * Bachelor of Arts in Government — College Factual / Political-Science-Schools;
  * Bachelor of Arts in Computer Science — Niche / Times Higher Education;
  * Bachelor of Engineering (ABET B.E.) — Dartmouth Engineering / U.S. News Thayer.

Each review is gathered from coverage ABOUT THAT PROGRAM (no synthesis from metadata),
carries program-distinct themes INCLUDING cautions, and cites resolvable third-party
sources. Programs with genuinely no program-specific third-party coverage keep
``external_reviews.summary`` in ``_standard.omitted`` (unchanged).

Idempotent: re-applies ``dartmouth_profile.apply()`` and re-derives program-preference
rows.

Revision ID: dartreviews1
Revises: bcgradtuition1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import dartmouth_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dartreviews1"
down_revision = "bcgradtuition1"
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
