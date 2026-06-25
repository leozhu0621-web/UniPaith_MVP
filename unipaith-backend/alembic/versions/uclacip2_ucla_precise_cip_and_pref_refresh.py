"""UCLA precise CIP-2020 codes + program-preference field refresh (REPAIR_BACKLOG #1 follow-up)

``uclacip1`` (#1141) filled UCLA ``cip_code`` at the 2-digit-family granularity (``NN.NN``)
and called ``backfill_program_preferences`` — but that helper only INSERTS missing
preference rows and fills EMPTY keys on existing ones; it never recomputes ``pref_fields``
on the derived rows ``progprefbf1`` created while ``cip_code`` was still NULL. So UCLA's
program -> student field signal stayed field-blind for every program whose field is
recoverable only from the CIP.

This follow-up:
  1. upgrades ``ucla_profile._CIP_BY_FIELD`` to verified NCES CIP-2020 4-digit codes
     (``NN.NNNN``) that each EXIST in ``data/reference/ref_majors.jsonl`` for the program's
     real field — so the CIP resolves to the SPECIFIC ``ref_majors`` entry (and its SOC
     career crosswalk), not just the family header. Every code was checked against the
     reference file (0 missing, correct titles); the 2-digit family the live matcher reads
     is unchanged, so this is a precision upgrade with no matcher-score regression. Fixes the
     coarse area-studies / legal-studies / real-estate joins (Codex review on #1142).
  2. deletes UCLA's stale DERIVED preference rows and re-derives them so ``pref_fields`` /
     ``pref_levels`` reflect the now-populated ``cip_code``. Claimed/first-party rows are
     never touched (authority precedence holds).

Idempotent: re-applies ``ucla_profile.apply()`` and re-derives the preference rows.

Revision ID: uclacip2
Revises: uclacip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclacip2"
down_revision = "uclacip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ucla_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucla_profile.INSTITUTION_NAME)
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
