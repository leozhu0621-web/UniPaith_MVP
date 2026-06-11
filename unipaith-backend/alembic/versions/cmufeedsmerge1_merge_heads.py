"""Merge dual heads (cmuprof1 + feedsforce1) — unblock deploys.

Two concurrent sessions chained migrations off sibling parents (the CMU
profile enrichment and the feeds zero-news fix), leaving two alembic heads.
No-op merge revision; both branches' schema changes are already applied in
order on upgrade.

Revision ID: cmufeedsmerge1
Revises: cmuprof1, feedsforce1
"""

from __future__ import annotations

revision = "cmufeedsmerge1"
down_revision = ("cmuprof1", "feedsforce1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
