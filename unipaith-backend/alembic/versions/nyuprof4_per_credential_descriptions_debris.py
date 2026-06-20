"""NYU — per-credential researched descriptions + scrape-debris removal (CRITICAL #2).

Re-applies ``nyu_profile.apply()`` after the data module gained ``_RESEARCHED_DESCRIPTIONS``
hand-authored, per-program bodies for the rows where the bulletin scrape had either reused a
single department paragraph across a field's credential siblings (a frame-shared body the
disambiguator could not split — e.g. Chemistry BA/BS shared ~950 chars, plus Classics, Math,
Physics, Italian, and the Tandon engineering pairs) or left raw catalogue debris in the prose
(contact blocks ``…@nyu.edu``, ``Warren Weaver Hall`` address fragments, and colon-truncated
requirement lists on History/Sport Management/Food Studies/Civil Engineering and others). Each
override is researched from that program's own NYU Bulletin page, distinct across credential
levels, and free of debris tells. Also renames two real joint majors (Anthropology and
Classical Civilization / Anthropology and Linguistics) and de-duplicates the redundant
"— Physical/Occupational Therapy" name echoes on the post-professional DPT/OTD rows.

Net effect on the live catalog: corrected frame-stripped shared-body = 0, scrape-debris = 0,
machine-artifacts = 0, every program conformant-or-omitted (anti-stub gate clean).

Also derives ``program_preferences`` for every NYU program (skips claimed rows) so the
program -> student match direction fires.

Revision ID: nyuprof4
Revises: uiucheadmrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyuprof4"
down_revision = "uiucheadmrg1"
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
