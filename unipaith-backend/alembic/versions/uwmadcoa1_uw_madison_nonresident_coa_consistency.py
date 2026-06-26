"""UW-Madison non-resident COA consistency (PR #1193 review follow-up).

PR #1193 switched the undergraduate matcher ``tuition`` scalar (and ``cost_data.tuition_usd``)
to the non-resident (out-of-state) rate, but left the top-level
``cost_data.total_cost_of_attendance`` at the resident COA — so non-resident undergraduate
rows read a total cost BELOW tuition alone (e.g. CS tuition $44,210 vs COA $28,679), which any
UI/ranking reading the COA would understate. This re-applies ``uw_madison_profile.apply()``
after rebasing the top-level COA to the non-resident figure (living/other is residency-invariant,
derived from the published resident COA minus the resident base tuition) and carrying BOTH
residency COAs in ``cost_data.breakdown``. Data-only; idempotent; no schema change.

Direct apply (no lock-bounded skip) so the corrected cost lands; verify-live on content.

Revision ID: uwmadcoa1
Revises: uwmadcipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile

revision = "uwmadcoa1"
down_revision = "uwmadcipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_madison_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
