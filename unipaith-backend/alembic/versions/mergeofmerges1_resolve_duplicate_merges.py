"""Resolve the duplicate-merge race: two sessions each shipped a merge migration
for the same dual-head pair (feedsbackfill1 + pennprof3) — #422 feedspennmerge1
and #424 mergepf3fb1 — which itself created a new dual head and blocked deploys.
This merge-of-merges restores a single head while keeping both prior merge files
valid for anything built on either.

Revision ID: mergeofmerges1
Revises: feedspennmerge1, mergepf3fb1
"""

revision = "mergeofmerges1"
down_revision = ("feedspennmerge1", "mergepf3fb1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
