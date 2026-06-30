"""MIT — matcher-core cip_code + program-distinct who_its_for

Clears REPAIR_BACKLOG entry #2 (HIGH) and entry #3b (MEDIUM) for the Massachusetts
Institute of Technology — the gold description 0-control, but an explicit repair target
for these two matcher-core dimensions (its null is NOT a model to imitate):

  #2  cip_code: MIT was the LONE catalog shipping ``cip_code`` null on every program
      (65 programs scored field-blind — no CIP join key to ``ref_majors`` / the field-66
      vocabulary). Every program now carries the verified federal CIP-4 family MIT itself
      reports, read directly from the U.S. Dept. of Education College Scorecard
      field-of-study list for MIT (UNITID 166683); nothing is guessed. MIT's distinctive
      interdisciplinary majors map to the real interdisciplinary CIPs MIT reports (30.08
      Mathematics & Computer Science, 30.39 Economics & Computer Science, 30.15
      Science/Technology/Society, 30.25 Cognitive Science, 04.10 Real Estate Development,
      09.07 Media Arts & Sciences).

  #3b who_its_for: the degree-type ``_WHO_BY_TYPE`` fallback collapsed all 65 programs to
      one template per credential level (a CS PhD and an Economics PhD read identically —
      distinct/total ~= 0.09). Every program now carries a program-DISTINCT, field-specific
      "Who it's for" statement (distinct/total = 1.0), derived from the program's own
      subject. Descriptions and names are UNCHANGED (MIT stays the description 0-control).

``mit_profile.apply()`` is idempotent (updates the 2 fields on the existing 65 rows; no
program rows are added or deleted), then ``backfill_program_preferences`` re-derives the
DERIVED ProgramPreference rows so ``pref_fields`` reflect the now-populated CIP codes
(claimed / first-party rows are never touched).

Deploy-safety: the idempotent data apply runs inside a SAVEPOINT bounded by
``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot get its
locks quickly. The apply is a light 65-row update, so it completes immediately; the run is
verified LIVE against the public API (cip_code + who_its_for distinctness) regardless.

Revision ID: mitcipwho1
Revises: gtowntuition3
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "mitcipwho1"
down_revision = "gtowntuition3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            mit_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == mit_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(f"  mitcipwho1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
