"""Cornell per-credential bodies — drop credential-frame + shared field-clause body

Cornell's catalog descriptions led each credential level with a generic frame
("Master's students in {field} complete graduate seminars …", "Ph.D. training in
{field} centers on …") before ONE shared FIELD_DESCRIPTIONS fact, so once the frame
was stripped 70 multi-credential fields still shared a body (REPAIR BACKLOG #13 /
miss #8 credential-frame). This re-applies ``cornell_profile.apply()`` with the field
fact leading and a distinct per-credential ``_cornell_level_body`` after it, so each
credential level carries its own researched body (gold MIT = 0% frame-stripped shared
body). The "David A. Duffield College of Engineering" naming is verified-correct
(Cornell renamed the college in January 2026 after a record $371.5M gift) and is
intentionally left intact. Idempotent; re-derives target-applicant rows.

Revision ID: cornellpercred1
Revises: bupercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellpercred1"
down_revision = "bupercred1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == cornell_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
