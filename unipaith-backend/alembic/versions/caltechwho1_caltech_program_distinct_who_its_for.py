"""Caltech program-distinct who_its_for (REPAIR_BACKLOG #3b).

Clears Caltech's who_its_for type-gaming: the catalog shipped one degree-type template
per tier (all 24 bachelor's rows read "Undergraduates seeking a deeply rigorous grounding
in science and engineering.", all 16 PhD rows read "Aspiring scholars pursuing an academic
or research career (fully funded).") plus two null master's rows (M.S. Aeronautics, M.S.
Electrical Engineering) whose degree_type had no _WHO_BY_TYPE fallback — so only 3 distinct
who_its_for strings covered 43 programs (a CS PhD and a Physics PhD read identically).

``_WHO_BY_SLUG`` now carries a field-specific 1-2 sentence statement (subject · who it
suits · typical trajectory) for every one of the 43 programs, grounded in each option's
real character (division, funded PhDs, named labs already cited in the descriptions —
GALCIT, the Seismological Laboratory, the Chen Institute, LIGO, JPL ties). Distinctness is
now 43/43 (≈1.0) and the two master's nulls are filled. No fabrication: who_its_for is a
characterization of applicant fit derived from each program's published nature, not an
invented statistic.

Re-applies ``caltech_profile.apply()`` (idempotent, replace=True) and re-derives
program-preference rows.

Revision ID: caltechwho1
Revises: bostoncollegeprof1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "caltechwho1"
down_revision = "bostoncollegeprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    caltech_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == caltech_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
