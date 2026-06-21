"""Stanford researched graduate descriptions + dual-head merge (REPAIR BACKLOG run 72 CRITICAL #1).

The run-68 "per-credential bodies" fixup replaced Stanford's shared discipline body with a
fixed per-credential TEMPLATE — "Graduate coursework in the {credential} emphasizes
{field-phrase}, with seminars, methods training, and a culminating thesis or capstone through
{School}." — that doubled the credential, slotted a field phrase, and appended a universal
field-agnostic tail. That manufactured 51 ``template_slot_artifacts`` rows shipped live
(Stanford was CERTIFIED_CLEAN but excluded from the template-slot gate). ``_assign_descriptions``
now uses hand-authored, researched graduate descriptions (``_GRADUATE_DESCRIPTION_BY_SLUG``) for
all 51 rows — each a true field fact plus the program's real verified Stanford department/school —
so ``template_slot_artifacts`` and ``frame_stripped_shared_body(abs_chars=150)`` both reach the
gold-MIT 0. Re-applies ``stanford_profile.apply()`` and re-derives program-preference rows.

Chains off ``pennuclamerge1`` (a concurrent session, #1034, already merged the dual head
``pennpercrd1`` + ``uclajhurelay1``), so ``main`` carries exactly one head.

Revision ID: stanfordpercrd2
Revises: pennuclamerge1
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
down_revision = "pennuclamerge1"
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
