"""enrich Columbia University profile — resume run (five more schools, data-only, no DDL)

Resumes Columbia's verified-partial tree per the routine's resumption design for large
universities. The first run (``columbiaprof1``) shipped the institution + five schools +
13 programs; this run adds five more of Columbia's real degree-granting schools — Columbia
Law School (founded 1858), the Mailman School of Public Health (1922), the School of
Nursing (1892), the Graduate School of Architecture, Planning and Preservation / GSAPP
(1881), and the School of Social Work (1898) — each with sourced About-tab detail (dean,
founding, research centers), plus one verified flagship program apiece (the J.D., MPH, the
Master's Direct Entry MS in Nursing, the M.Arch, and the M.S. in Social Work). Program
outcomes are the College Scorecard Field-of-Study median earnings by CIP for UNITID 190150;
program tuition is published only on JavaScript-rendered Bursar pages and is honestly
omitted (recorded in each node's ``_standard.omitted``).

It re-invokes ``unipaith.data.columbia_profile.apply()`` — fully idempotent and
partial-safe (it never deletes Columbia schools/programs it does not own, keys schools off
``(institution_id, name)`` and programs off ``slug``), and a no-op when Columbia is absent,
so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations). It ships to production automatically: the
container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: columbiaprof2
Revises: columbiaprof1
Create Date: 2026-06-10
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof2"
down_revision = "columbiaprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    columbia_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass
