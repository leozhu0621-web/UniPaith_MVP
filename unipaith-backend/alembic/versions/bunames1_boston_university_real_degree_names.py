"""Boston University — real degree names, cleaned tracks, full-tier tuition (REPAIR run 74).

Finishes BU on top of #1054 (``buconc1``). #1054 cleared the nine em-dash rows but left
several structural / matcher defects this migration clears (miss #2 + matcher-core tuition):

- **Mislabeled combined BA/MA degrees** — nine CAS rows the name-generator called
  "Master of Science in {field}" (a credential lie) are renamed to their VERIFIED conferred
  M.A. (Archaeology, Astronomy, Biotechnology, Chemistry, Classical Studies, English,
  International Affairs, Linguistics, Physics — each checked against bu.edu/academics).
- **Two #1054 credential errors corrected** — the Energy & Environment programs confer the
  M.S. (not "M.A. in Earth & Environment") and the Remote Sensing program is a distinct
  "M.S. in Remote Sensing & Geospatial Sciences"; the GRS Energy & Environment standalone +
  the MET M.S. in Applied Data Analytics are restored as distinct degrees the collapse
  heuristic had eaten.
- **"Master of Science in Ms" + stub** (CDS BS-to-MS in Data Science) and the GMS
  Genetics & Genomics row (mislabeled "MD/PhD", was ``professional``) get real names, a
  researched description, and the correct ``phd`` degree type.
- **Garbage ``tracks``** (credential-token scrape artifacts like "Ma", "Bama In Linguistics",
  "Master Of Science In Biology", the MFA-translation languages bleeding into Romance Studies)
  are sanitized; MSCIS gets its eight verified published concentrations.
- **Funded-PhD tuition** now stamps the published sticker (matcher budget input) instead of
  ``$0`` — funding stays a separate ``funded``/``note`` signal — so the whole PhD tier is
  covered (was 30/76).

Re-applies ``bu_profile.apply()`` (idempotent — ``_apply_programs`` deletes the now-stale
collapsed concentration rows) and re-derives program-preference rows.

Revision ID: bunames1
Revises: buconc1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bunames1"
down_revision = "buconc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # Drop the DERIVED (never claimed/first-party) target-applicant rows BEFORE re-apply so
        # renamed keepers re-derive fresh preferences and the newly-collapsed concentration
        # programs lose their generated dependent, letting ``_apply_programs`` delete them
        # cleanly. Real student data (saved lists / applications) keeps a row unpublished.
        bu_prog_ids = select(Program.id).where(Program.institution_id == inst.id)
        session.execute(
            delete(ProgramPreference).where(
                ProgramPreference.program_id.in_(bu_prog_ids),
                ProgramPreference.source == "derived",
            )
        )
        session.flush()
    bu_profile.apply(session)
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
