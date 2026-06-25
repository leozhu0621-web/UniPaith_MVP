"""UCLA cip_code per program (matcher field-signal — REPAIR_BACKLOG #1)

Clears the matcher-core ``cip_code`` starvation for UCLA: the column is now
serialized on ``GET /programs/{id}`` and is the CIP join key the CPEF matcher uses
to resolve a program's field to ``ref_majors`` + the field-66 vocabulary (the
interest/field signal alongside the dense ``description_text`` embedding), yet UCLA
shipped it NULL on all 372 programs, scoring every one field-blind on the CIP key.

``ucla_profile`` now stamps each program's 4-digit CIP-2020 family (``NN.NN``) from
``_CIP_BY_FIELD`` — every code is one UCLA actually reports to IPEDS for UNITID
110662 (U.S. Dept. of Education College Scorecard, ``latest.programs.cip_4_digit``),
mapped by field name, never guessed. Coverage is 100% (372/372); a genuinely
uncodeable field would be recorded in ``_standard.omitted`` instead.

Idempotent: re-applies ``ucla_profile.apply()`` (which now assigns ``p.cip_code``)
and re-derives program-preference rows.

Revision ID: uclacip1
Revises: nyumastertuition1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclacip1"
down_revision = "nyumastertuition1"
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
        # Cover any program that still lacks a derived ProgramPreference row. We do NOT
        # force-refresh the existing derived rows: the matcher reads the corrected field
        # signal from Program.cip_code directly (4-digit → ref_majors, e.g. 45.02 =
        # Anthropology). ProgramPreference.pref_fields would instead be re-derived through
        # fields_offered_for_program's COARSE 2-digit CIP-family fallback (family 45 →
        # "political_science" head), which on the 63 UCLA rows whose names don't
        # canonicalize would REPLACE today's honest omission with a wrong field
        # (Anthropology/Sociology/Geography → political_science) — an omit-never-guess
        # regression. So leave the correctly-omitted pref_fields untouched.
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
