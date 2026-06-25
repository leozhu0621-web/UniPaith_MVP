"""UCSD matcher-core cip_code + graduate de-fabrication + MBA tuition (REPAIR_BACKLOG #1)

Takes the UC San Diego catalog toward gold across three dimensions in one unit:

  1. **cip_code (REPAIR_BACKLOG #1, matcher-core).** Stamps every program's
     IPEDS-reported CIP-2020 family code (``NN.NN``, for UNITID 110680) onto
     ``Program.cip_code`` — the CIP join key the CPEF matcher resolves (by 2-digit
     family) to ``ref_majors`` + the field-66 vocabulary. The code was already carried on
     every spec for the breadth cross-check; this is a no-research fill. UCSD shipped
     ``cip_code`` NULL fleet-wide before this (the field is newly serialized).

  2. **Graduate de-fabrication (the inviolable no-fabrication rule).** The IPEDS
     CIP->name resolution had produced graduate names UC San Diego does not confer:
       • CIP 11.10 (Rady) -> "MS in Information Technology Management" — Rady offers no
         such degree (rady.ucsd.edu/programs) -> DROPPED.
       • CIP 52.08 (Rady) -> renamed to the real "Master of Quantitative Finance".
       • CIP 45.09 (GPS)  -> renamed to the real "Master of International Affairs".
       • CIP 51.07 (SoM)  -> renamed to the real "Master of Advanced Studies in
         Leadership of Healthcare Organizations" (lhco.ucsd.edu).
     Each renamed row gets a verified, field-specific description.

  3. **MBA tuition.** The Rady Full-Time MBA is state-supported and publishes a single
     annual tuition + fees figure ($52,058 resident / $57,201 nonresident, 2024-25
     registrar) on the same basis as the academic tiers — so it is now priced, not
     omitted. The remaining self-supporting per-unit master's (MS Business Analytics,
     Master of Quantitative Finance, Master of International Affairs, MPH, MAS-LHCO) keep
     tuition omitted-with-reason (no single published annual figure on this basis).

Re-derives the DERIVED program-preference rows so ``pref_fields`` reflects the now-populated
``cip_code`` (claimed/first-party rows are never touched — authority precedence holds).

Idempotent: re-applies ``ucsd_profile.apply()`` (replace/dedup) and re-derives preferences.
The dropped CIP 11.10 row is removed by ``apply`` (deletes non-canonical programs).

Revision ID: ucsdcipdefab1
Revises: penncipmph1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucsdcipdefab1"
down_revision = "penncipmph1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ucsd_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucsd_profile.INSTITUTION_NAME)
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
