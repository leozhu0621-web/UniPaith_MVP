"""Merge-of-merges: unify the columbiacip1 + cipmergeofmerges1 dual head

The auto-merge race recurred. Two PRs each set ``down_revision = (berkvandydartmerge1,
cip3waymerge1)`` to unify the prior duplicate 3-way merge heads, and **both landed**:

- ``cipmergeofmerges1`` (#1163) — an empty merge-of-merges, auto-merged on green CI;
- ``columbiacip1``       (#1164) — the same head-unification carrying Columbia's
  matcher-core ``cip_code`` data, merged moments later.

So ``main`` again has two parallel merge heads, which fails
``test_alembic_has_single_head`` and blocks every ``Deploy Backend`` run. This empty
merge-of-merges reunites the two into a single head ``cipheadunify86`` so deploys ship
again. Graph-only: no schema or data changes (Columbia's data already rides
``columbiacip1`` in the upgrade path).

Revision ID: cipheadunify86
Revises: cipmergeofmerges1, columbiacip1
Create Date: 2026-06-25
"""

from __future__ import annotations

revision = "cipheadunify86"
down_revision = ("cipmergeofmerges1", "columbiacip1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
