"""Harvard profile repair — coverable external_reviews on nine more programs.

Re-applies ``unipaith.data.harvard_profile.apply()`` so nine additional coverable
programs gain aggregated, cited ``external_reviews`` (MBAn shape): the HKS MPA and
MPA/ID, the HGSE Ed.M., the HLS LL.M., the GSD Master in Landscape Architecture, the
HDS Master of Divinity and Master of Theological Studies, the Harvard Extension ALM,
and the Economics PhD. Each carries a summary, 4-6 themes (including the common
cautions), and >=2 resolvable third-party sources. Idempotent: ``apply()`` upserts
by name/slug and re-stamps each program's ``_standard`` (the reviewed programs drop
``external_reviews.summary`` from their omitted lists). No-op on a DB without Harvard.

Revision ID: harvardrev1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardrev1"
down_revision = "onboardstate1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
