"""Dartmouth — finish the Guarini catalog + matcher-core cip_code + universal who_its_for

Finishes the in-flight Dartmouth deferral and clears its open REPAIR_BACKLOG entries:

  * BREADTH (#2 in-flight): adds the full Guarini graduate catalog the prior pass deferred
    — Math / Earth Sciences / EEES / MCB / QBS / Computational Science & Modeling /
    Integrative Neuroscience / Health Policy & Clinical Practice PhDs; Chemistry MS,
    Comparative Literature MA, Earth Sciences MS, MFA in Sonic Practice; the five
    Geisel-based health-sciences master's (Epidemiology, Health Data Science, Healthcare
    Research, Implementation Science, Medical Informatics); and the Master of Energy
    Transition — taking the catalog from 43 to 61 real, distinctly-named programs.
  * cip_code (#1): stamps the IPEDS CIP family on EVERY program (the matcher's interest/
    field join key), previously null fleet-wide for Dartmouth.
  * who_its_for (#4): a field-specific audience statement on EVERY program (universal-depth
    field), previously null.
  * external_reviews (#5): adds a sourced Geisel M.D. review alongside the Tuck MBA.
  * tuition: the new Guarini full-time research master's carry the published $95,596 rate;
    the per-credit/online Geisel master's + the new MET are honest omit-with-reason; PhDs
    stay funded-omit. Never the undergrad sticker copied down.

All values are verified-or-omitted and stamped in ``dartmouth_profile``. Idempotent:
re-applies ``apply()`` and re-derives program-preference rows.

Revision ID: dartfinish1
Revises: berkeleycip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import dartmouth_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dartfinish1"
down_revision = "berkeleycip1"
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
