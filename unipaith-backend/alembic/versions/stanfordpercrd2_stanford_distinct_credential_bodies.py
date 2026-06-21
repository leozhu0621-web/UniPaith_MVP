"""Stanford template-slot grammar repair (REPAIR BACKLOG run-72 CRITICAL #1).

The run-68 "per-credential" builder (stanfordpercrd1) fell back to a fixed template that
DOUBLED the credential and slotted a field blurb ("Graduate coursework in the Master of
Science in Chemistry emphasizes ...") on 51 graduate rows whose siblings shared a body —
machine grammar a student reads (``template_slot_artifacts``). ``_assign_descriptions`` now
serves a researched, level-specific body (``_GRADUATE_DESCRIPTIONS``) for each of those 51
programs: concrete disciplinary subfields anchored to the real Stanford school, no credential
restated in the body, no universal tail, no body shared with a sibling. The whole catalog now
scores the gold-MIT zero on ``template_slot_artifacts``, ``analyze``, and
``frame_stripped_shared_body(abs_chars=150)``. Re-applies ``stanford_profile.apply()`` and
re-derives program-preference rows.

Revision ID: stanfordpercrd2
Revises: uclaberkmerge1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "stanfordpercrd2"
down_revision = "uclaberkmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == stanford_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
