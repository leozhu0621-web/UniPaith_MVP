"""Merge the dual head AND refresh derived ProgramPreference GPA floors.

Two jobs in one migration:

1. **Merge heads** — unifies the concurrent ``aivisamerge1`` + ``columbiapercred1``
   heads into a single head (concurrent enrichment PRs left two heads; the deploy
   tolerates them via ``alembic upgrade heads`` but a single head is the standard).

2. **Refresh derived GPA floors** — the derived ``ProgramPreference`` rows backfilled
   fleet-wide by ``progprefbf1`` carried no ``pref_min_gpa`` because the derivation read
   the (empty) typed ``ProgramAdmissionsHistory.class_profile`` and probed only the
   ``gpa_p25``/``gpa_p50`` keys, while the populated data lives in the editorial
   ``Program.class_profile`` JSONB under ``median_gpa`` / ``avg_gpa``. ``derive_preferences``
   now reads both; this migration:
     - ``backfill_program_preferences`` — derive a row for any program still missing one
       (newly-enriched programs since progprefbf1), and
     - ``refresh_derived_gpa_floors`` — set ``pref_min_gpa`` on existing ``source='derived'``
       rows that lack it, from the JSONB class profile.
   So the program -> student GPA signal (``cpef_program_to_student`` reads ``pref_min_gpa``)
   finally fires for flagship programs that publish a class GPA.

Authority-safe + idempotent: both helpers touch only derived rows that lack the value;
claimed/first-party rows and already-set values are never overwritten; re-running is a
no-op.

Revision ID: progprefgpa1
Revises: aivisamerge1, columbiapercred1
Create Date: 2026-06-20

"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op

# revision identifiers, used by Alembic.
revision = "progprefgpa1"  # pragma: allowlist secret
down_revision = ("aivisamerge1", "columbiapercred1")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Lazy import so `alembic heads`/discovery never imports the matcher stack.
    from unipaith.services.match.derive_preferences import (
        backfill_program_preferences,
        refresh_derived_gpa_floors,
    )

    session = Session(bind=op.get_bind())
    backfill_program_preferences(session)  # any program still lacking a derived row
    refresh_derived_gpa_floors(session)  # fill pref_min_gpa on existing derived rows from JSONB
    session.flush()


def downgrade() -> None:
    # Data-only, forward-only refresh — no clean inverse (we cannot tell which derived
    # rows were NULL before). progprefbf1.downgrade still removes all derived rows.
    pass
