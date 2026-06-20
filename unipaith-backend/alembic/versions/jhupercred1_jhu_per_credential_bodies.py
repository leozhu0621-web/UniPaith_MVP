"""JHU per-credential bodies — drop credential-frame + shared field-clause body

Johns Hopkins's catalog descriptions led each credential level with a generic frame
("Johns Hopkins offers the undergraduate major in {field}.", "Doctoral study in
{field} … centers on dissertation research.") before ONE shared FIELD_DESCRIPTIONS
fact, so once the frame was stripped 81/82 multi-credential fields still shared a body
(REPAIR BACKLOG #5 / miss #8 credential-frame + tail-shared field body). This
re-applies ``jhu_profile.apply()`` with the verified field fact leading and a distinct
per-credential ``_level_body`` after it, so each credential level (BA / MS /
certificate / PhD) carries its own researched body (gold MIT = 0% frame-stripped
shared body). It also de-roll-ups the residual CIP 05.01 "Area Studies" rows: the BA
is renamed to its real degree ("Bachelor of Arts in Latin American, Caribbean, and
Latinx Studies") and the IPEDS-minted MS + certificate rows are dropped (JHU confers
no master's or certificate in that field). Idempotent; re-derives target-applicant
rows.

Follows ``usccornellmrg1`` (the merge of ``uscdebris2`` + ``cornellpercred1``) so
``main`` stays at exactly one Alembic head.

Revision ID: jhupercred1
Revises: usccornellmrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "jhupercred1"
down_revision = "usccornellmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    jhu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == jhu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
