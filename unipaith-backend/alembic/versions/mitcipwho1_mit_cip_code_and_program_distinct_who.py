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
program rows are added or deleted). Because the populated ``cip_code`` / ``who_its_for``
change the program-side match signal, this migration follows the canonical cip/who-repair
pattern (``bucipwho1`` / ``nyucipwho1``): the unclaimed ``source="derived"``
ProgramPreference rows are DELETED and re-derived (``backfill_program_preferences`` only
fills empty keys on an existing row, so it would NOT refresh stale ``pref_fields`` that the
fleet-wide ``progprefbf1`` backfill derived while ``cip_code`` was null — the rows must be
dropped first), and every cached ``MatchResult`` for an MIT program is marked stale +
``Program.feature_version`` is bumped so the rationale/embedding caches invalidate and
``GET /me/matches`` rescores against the corrected data. Claimed / first-party rows are
never touched. Direct apply (no lock-bounded skip) — the cip/who-repair convention — and
the result is verified LIVE against the public API regardless.

Revision ID: mitcipwho1
Revises: gtowntuition3
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "mitcipwho1"
down_revision = "gtowntuition3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    mit_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == mit_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        all_prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        # Preference re-derivation must NOT touch first-party (claimed) rows. Drop the
        # unclaimed DERIVED rows so the backfill re-derives pref_fields from the now-stamped
        # cip_code (backfill skips a program that already has a row, so without the delete
        # the stale fleet-wide-derived pref_fields would survive).
        unclaimed_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if unclaimed_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(unclaimed_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
        if all_prog_ids:
            # Bump feature_version so the rationale cache (keyed on program_version) and the
            # lazy embedding rebuild (embedding_version != feature_version) both invalidate
            # against the corrected cip_code / who_its_for, then mark every cached
            # MatchResult stale so GET /me/matches rescores against fresh data.
            session.execute(
                Program.__table__.update()
                .where(Program.id.in_(all_prog_ids))
                .values(feature_version=Program.feature_version + 1)
            )
            session.execute(
                MatchResult.__table__.update()
                .where(MatchResult.program_id.in_(all_prog_ids))
                .values(is_stale=True)
            )
    session.flush()


def downgrade() -> None:
    pass
