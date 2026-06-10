"""merge feedsbackfill1 and pennprof3 heads

Two data-only migrations branched off ``pennprof2`` in parallel and both landed on
``main``: ``feedsbackfill1`` (institution feeds backfill) and ``pennprof3`` (the Penn
graduate/professional flagship programs). That left the chain with two heads, which
trips the single-head compliance check (``test_spec_03_compliance``) and the
``enrich-profile`` routine's health check, and aborts the backend deploy. This empty
merge migration reunites them into a single head so ``alembic upgrade head`` resolves
again. No schema or data changes — both parents are independent data enrichments that
have already run.

Revision ID: mergepf3fb1
Revises: feedsbackfill1, pennprof3
Create Date: 2026-06-10
"""

from __future__ import annotations

revision = "mergepf3fb1"
down_revision = ("feedsbackfill1", "pennprof3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Empty merge — unifies two independent data-only heads into one.
    pass


def downgrade() -> None:
    # Nothing structural to roll back.
    pass
