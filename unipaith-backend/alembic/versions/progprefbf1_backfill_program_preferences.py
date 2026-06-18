"""Backfill derived ProgramPreference for the whole fleet.

Its data step derives a baseline target-applicant ``ProgramPreference`` (AI Structure
Spec 2 §3.4) for EVERY program that lacks one — so the program -> student CPEF
direction fires fleet-wide. Until now no program carried a preference row, so that
direction was inert ("no opinion") for all ~300 universities. The derivation is
deterministic + grounded-only (canonical field from name/CIP, eligible applicant
levels from the degree, GPA floor from a real class profile — omit-never-guess) and
stamps ``source="derived"`` / ``confidence=0.4`` (the Spec 2 §3.6 inferred authority
tier feeding ``c_program``).

Idempotent + authority-safe: a program that already has a (derived OR claimed) row is
skipped — first-party data is never overwritten, and re-running inserts nothing.

Chains off ``uclaprof5`` (the current single head — it already merged the prior
gendlock3mo/uclaprof4 split), keeping a single Alembic head.

Revision ID: progprefbf1
Revises: uclaprof5
Create Date: 2026-06-18

"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from alembic import op

# revision identifiers, used by Alembic.
revision = "progprefbf1"  # pragma: allowlist secret
down_revision = "uclaprof5"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Lazy import so `alembic heads`/discovery never imports the matcher stack.
    from unipaith.services.match.derive_preferences import backfill_program_preferences

    session = Session(bind=op.get_bind())
    backfill_program_preferences(session)  # whole fleet; skips existing/claimed rows
    session.flush()


def downgrade() -> None:
    # Remove only the rows this routine derived; never touch claimed/first-party rows.
    op.execute(text("DELETE FROM program_preferences WHERE source = 'derived'"))
