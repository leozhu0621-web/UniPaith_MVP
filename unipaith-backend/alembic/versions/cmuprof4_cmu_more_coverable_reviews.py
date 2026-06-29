"""Carnegie Mellon profile repair — coverable external_reviews depth pass (batch 2)

Re-applies ``unipaith.data.carnegie_mellon_profile.apply()`` so 13 additional
coverable programs — Heinz analytics & public-policy master's (MISM-BIDA, MADS,
MSPPM Data Analytics / D.C., Health Care Analytics), the joint CFA programs
(MEIM, Master of Arts Management), Tepper/MCS computational finance (BSCF),
Dietrich statistics (MS Statistics + the Statistics and Statistics-and-ML
bachelor's), and the College of Fine Arts architecture degrees (B.Arch,
M.Arch) — gain aggregated, cited ``external_reviews`` in the MBAn shape.
Idempotent: ``apply()`` upserts by slug and is a no-op when CMU is absent
(fresh / CI databases).

Revision ID: cmuprof4
Revises: campusgallery1
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof4"
down_revision = "campusgallery1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    carnegie_mellon_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
