"""merge the cmuprof1 + feedsforce1 alembic heads into one

Two data-only migrations (cmuprof1 — Carnegie Mellon profile; feedsforce1 —
zero-news feed fix) both branched off ``cornellprof1`` and merged to main
concurrently, leaving the tree dual-headed. This is a merge-only migration
(no DDL, no data) that re-unifies them so ``alembic upgrade head`` resolves to a
single head and deploys are unblocked.

Revision ID: cmufeedsmerge1
Revises: cmuprof1, feedsforce1
Create Date: 2026-06-11
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
