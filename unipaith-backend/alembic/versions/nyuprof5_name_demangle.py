"""NYU — de-mangle scrape-stripped program names (REPAIR BACKLOG CRITICAL #1).

The bulletin scrape that seeded the NYU catalog dropped conjunctions, commas,
parentheses, and grade-band dashes from multi-field and teacher-certification titles,
so the slug derivation produced space-mashed program names the student saw as the page
heading: joint majors ("Economics Computer Science" → "Economics and Computer Science",
"French Linguistics" → "French and Linguistics", "Global Public Health Anthropology" →
"Global Public Health and Anthropology"), Steinhardt teacher-certification titles
("Teaching Chemistry 7 12" → "Teaching Chemistry, Grades 7–12", "Teachers English 7 12" →
"Teachers of English, Grades 7–12"), Stern programs ("Business Political Economy" →
"Business and Political Economy"), LL.M. specializations, the Carter journalism dual
degrees, the Institute of French Studies / History joint PhDs, and the Meyers nursing
pathways. Each restored name is the official NYU Bulletin title, verified against the
program's own bulletin page / first-party description. Also fixes the French Studies and
French PhD description, which the scrape had mis-assigned the French Studies/History body.

Re-applies ``nyu_profile.apply()`` (idempotent, slug-keyed) so the live catalog picks up
the corrected ``program_name`` / ``description`` values, then re-derives
``program_preferences`` (skips claimed rows) so the program -> student match still fires.

Revision ID: nyuprof5
Revises: harvardpercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyuprof5"
down_revision = "harvardpercred1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
