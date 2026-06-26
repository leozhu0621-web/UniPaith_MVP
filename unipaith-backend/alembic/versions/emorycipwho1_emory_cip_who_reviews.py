"""Emory cip_code (REPAIR_BACKLOG #1) + who_its_for (#4) + reviews depth (#5)

Three matcher / universal-depth repairs on Emory's already-real 46-program catalog (names,
departments, and field-specific descriptions were already structurally clean; the catalog
STRUCTURE and tuition are untouched here):

  1. ``cip_code`` (matcher-core CIP join key to ref_majors + the field-66 vocabulary): Emory's
     ``apply()`` never stamped ``p.cip_code``, so the catalog shipped ``cip_code`` null
     fleet-wide and the matcher scored those programs field-blind. Now stamps the standard
     IPEDS CIP-2020 code for each program's field (``_CIP_BY_SLUG``, 46/46) — a published
     taxonomy lookup, never a guess.

  2. ``who_its_for`` (universal-depth field, run-84/86 rule): the catalog shipped this field
     0% live because the ``apply()`` loop hard-set ``p.who_its_for = None``. It now stamps a
     per-program, field-specific applicant statement (``_WHO_BY_SLUG``, 46/46), each naming the
     applicant the program fits — never a classification stub. Restores the field to 100%.

  3. ``external_reviews`` depth (#5): adds program-specific, third-party-sourced reviews for the
     coverable professional / graduate / flagship-undergrad programs (Rollins MPH, Nell Hodgson
     BSN, Emory Law JD, Emory School of Medicine MD, Goizueta BBA) beside the existing MBA
     review — each gathered from real coverage (U.S. News, Poets&Quants, school ranking news),
     with cautions and resolvable sources. Programs with no third-party coverage keep their
     honest ``external_reviews`` omission.

Idempotent: re-applies ``emory_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched. The
apply runs DIRECTLY (no lock-bounded self-skipping SAVEPOINT), so a failure fails the deploy
rather than silently stranding the data not-live.

Revision ID: emorycipwho1
Revises: remindersent1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import emory_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "emorycipwho1"
down_revision = "remindersent1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    emory_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == emory_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        if prog_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(prog_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
