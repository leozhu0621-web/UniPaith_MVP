"""Boston University description slug-filler repair.

Re-applies ``bu_profile.apply()`` after replacing rendered catalog-slug filler
("degree listing ... set N" / "official catalog listing <slug>") with
source-specific descriptions from official BU Academics pages for the affected
Goldman SDM and Wheelock CAGS rows.

Re-derives unclaimed ProgramPreference rows, persists omission-only derived rows
for unclassifiable public programs such as ROTC certificates, and marks BU
MatchResults stale so matches rescore against the refreshed descriptions.

Revision ID: budescslug1
Revises: uvarev1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import (
    backfill_program_preferences,
    derive_program_preference,
)

revision = "budescslug1"
down_revision = "uvarev1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        all_prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
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
        existing_pref_program_ids = set(
            session.scalars(
                select(ProgramPreference.program_id).where(
                    ProgramPreference.program_id.in_(all_prog_ids),
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
        if all_prog_ids:
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
