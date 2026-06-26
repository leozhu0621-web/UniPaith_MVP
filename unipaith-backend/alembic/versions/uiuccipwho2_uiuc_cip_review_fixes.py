"""UIUC matcher-core review fixes — re-apply with corrected CIP codes + cost-card basis.

Follows up uiuccipwho1 with three reviewer-confirmed accuracy fixes (PR #1190 review):
  * Doctor of Audiology (AuD) -> CIP 51.0202 (Audiology/Audiologist), the AuD-specific code,
    not the general 51.0201 Communication Sciences and Disorders.
  * Gies College of Business "Information Systems" BS -> CIP 52.1201 (Management Information
    Systems), the business/MIS code, not 11.0401 Information Science (the iSchool family) —
    so its derived program-preferences target business, not computer-science, applicants.
  * Graduate/professional cost cards keep ``cost_data.tuition_usd`` on the labeled
    Illinois-resident basis (matching the verified note); only the flat matcher scalar
    ``program.tuition`` stays NON-RESIDENT (the skill's "only the exposed scalar is wrong").

Re-applies ``uiuc_profile.apply()`` directly and recomputes derived program_preferences (the two
re-coded programs need their field signal re-derived from the corrected ``cip_code``).

Revision ID: uiuccipwho2
Revises: uiuccipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uiuccipwho2"
down_revision = "uiuccipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uiuc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uiuc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        prog_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
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
