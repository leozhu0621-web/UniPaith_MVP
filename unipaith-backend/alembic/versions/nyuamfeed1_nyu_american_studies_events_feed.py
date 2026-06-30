"""NYU American Studies descriptions and events feed repair.

Re-applies the NYU profile after replacing the generic American Studies bulletin
fallback descriptions and adding NYU's current LiveWhale events iCal feed to
institution, school, and program content sources.

Revision ID: nyuamfeed1
Revises: harvfeed1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import (
    backfill_program_preferences,
    derive_program_preference,
)

revision = "nyuamfeed1"
down_revision = "harvfeed1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
        all_prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        existing_pref_program_ids = set(
            session.scalars(
                select(ProgramPreference.program_id).where(
                    ProgramPreference.program_id.in_(all_prog_ids)
                )
            ).all()
        )
        missing_unclaimed = session.scalars(
            select(Program).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
                Program.id.not_in(existing_pref_program_ids),
            )
        ).all()
        for prog in missing_unclaimed:
            pref = derive_program_preference(
                cip_code=prog.cip_code,
                program_name=prog.program_name or "",
                degree_type=prog.degree_type,
                class_profile=prog.class_profile,
                description=prog.description_text,
                outcomes_data=prog.outcomes_data,
                application_requirements=prog.application_requirements,
                source_url=prog.website_url or prog.source_url,
                allow_omission_only_target_profile=True,
            )
            if pref is not None:
                session.add(ProgramPreference(program_id=prog.id, **pref))
    session.flush()


def downgrade() -> None:
    pass
