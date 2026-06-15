"""New York University — gold-standard profile (institution + 17 schools + 507-program catalog).

Idempotent data migration: calls ``nyu_profile.apply()`` which upserts the institution's
ranking_data / school_outcomes / description / campus photos / content_sources, the 17 schools
(about_detail + content_sources), and the full 507-program bulletin catalog (basics + delivery
format + content_sources on every node, with per-program tuition/outcomes/reviews verified for
the flagship programs and honestly omitted-with-reason elsewhere). No-op when NYU is absent, so
it is safe on fresh / CI databases that have not run the catalog seed.

Revision ID: nyuprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile

revision = "nyuprof1"
down_revision = "onboardstate1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    nyu_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment; no schema change to reverse.
    pass
