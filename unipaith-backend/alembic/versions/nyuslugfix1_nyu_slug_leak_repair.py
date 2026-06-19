"""NYU — strip URL-slug-leak descriptions on cross-field joint/track families (CRITICAL #2).

Re-applies ``nyu_profile.apply()`` after the data module's cross-field disambiguation
was repaired: ``_disambiguate_catalog_descriptions`` block 3 used to prepend the kebab
URL slug (``"global-public-health-anthropology — …"``) to dodge the anti-stub cross-field
normalization, leaking a build artifact onto the live page (41 rows). It now leads each
joint-major / combined-degree / nurse-practitioner-track / teaching-subject sibling with
its real, name-grounded distinguishing specialization instead of the slug, so the
descriptions stay unique and field-specific with zero slug leak (anti-stub clean,
``machine_artifacts = 0``).

Also derives ``program_preferences`` for every NYU program (skips claimed rows) so the
program -> student match direction fires.

Revision ID: nyuslugfix1
Revises: uscprof4
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyuslugfix1"
down_revision = "uscprof4"
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
