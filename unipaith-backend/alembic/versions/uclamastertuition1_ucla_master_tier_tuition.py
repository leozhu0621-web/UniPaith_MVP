"""UCLA published master's-tier tuition + drop fabricated MSM (REPAIR_BACKLOG #3)

Clears the master's-tier tuition residual the catalog aggregate hid: UCLA's
bachelor's tier shipped 100% but 48 of 146 master's rows were null, starving the
matcher's graduate budget-fit signal. Those nulls were UCLA's school-billed
professional + self-supporting master's (Anderson MBA/EMBA/FEMBA/GEMBA/MFE/MSBA,
Fielding MPH/EMPH/MHA/MDSH, Geffen MS-DSB, Samueli MEng + online MSOL tracks,
Luskin MPP/MSW/MURP/MRED, Law LL.M./M.L.S., Education M.Ed./M.L.I.S., L&S applied
master's) — each PUBLISHES its own rate, so the nulls were skipped knowable fields,
not honest omissions. ``ucla_profile`` now stamps each program's real published
CA-resident annual rate (never the undergrad sticker, never the academic rate
copied down, never guessed), cited to the school's own tuition page. Only the
Film & Television M.F.A. stays omitted-with-reason (PDST-inclusive annual total not
published to a fetchable figure).

Also drops the fabricated "Master of Science in Management" row — UCLA Anderson
awards no such standalone master's (only the MFE and MSBA), confirmed against the
official Anderson degrees page. The real Ph.D. in Management is retained. The
idempotent ``apply()`` deletes the non-canonical program (or unpublishes it if it
has dependents).

Idempotent: re-applies ``ucla_profile.apply()`` and re-derives program-preference
rows.

Revision ID: uclamastertuition1
Revises: uwmadenggen1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclamastertuition1"
down_revision = "uwmadenggen1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ucla_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == ucla_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
