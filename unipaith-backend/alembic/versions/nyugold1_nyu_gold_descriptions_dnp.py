"""NYU gold repair: per-program descriptions + DNP collapse (REPAIR BACKLOG CRITICAL #1).

Gives every NYU joint major, CAS+Tandon dual degree, and per-subject/per-region/
per-language program its OWN researched description instead of a base department blurb
reused verbatim across cross-field rows (the cross-field stamp the field-keyed anti-stub
gate misses; gold MIT = unique per program). Also rewrites the "BA in Biochemistry"
body, which had inherited the Chemistry department-history paragraph with no
biochemistry-specific content, and collapses the six "Doctor of Nursing Practice —
{specialty}" concentration-split rows (miss #2) into one DNP carrying the specialties as
tracks. Re-applies ``nyu_profile.apply()`` (which reconciles the dropped DNP slugs) and
re-derives program-preference rows.

This revision also UNIFIES the pre-existing dual head on ``main`` (``colaivisamerge1`` +
``michaimrg1`` — the Columbia/Michigan per-credential merge race) so the tree returns to
a single head.

Revision ID: nyugold1
Revises: colaivisamerge1, michaimrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyugold1"
down_revision = ("colaivisamerge1", "michaimrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
