"""Berkeley cip_code + non-resident tuition RE-APPLY (berkeleycip1 was stamped-not-run)

berkeleycip1 carried the Berkeley matcher-core repair (cip_code on all programs,
public non-resident tuition scalar, CED master's tuition, legal-studies dedup), but
its data never reached production: the deploy entrypoint's ``alembic upgrade heads``
failed on the congested deploy and fell into the nuclear recovery path
(``docker-entrypoint.sh`` purges ``alembic_version`` and ``alembic stamp heads``),
which marks a migration applied WITHOUT running its ``upgrade()`` — silently freezing
this data-only migration (live API still served cip_code=null, bachelor tuition=16,347,
232 programs). Because berkeleycip1 is now stamped, a redeploy will not re-run it.

This fresh revision re-applies the same idempotent enrichment so the next deploy
actually lands it. ``berkeley_profile.apply()`` is idempotent (replace/dedup +
program reconcile); re-deriving program preferences first deletes the stale
cip-null derived rows so pref_fields reflect the now-populated CIP codes.

Revision ID: berkeleycip2
Revises: berkeleycip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleycip2"
down_revision = "berkeleycip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    berkeley_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == berkeley_profile.INSTITUTION_NAME)
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
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
