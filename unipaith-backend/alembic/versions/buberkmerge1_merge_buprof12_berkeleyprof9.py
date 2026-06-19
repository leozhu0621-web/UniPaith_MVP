"""Merge dual heads buprof12 + berkeleyprof9 (auto-merge race).

PR #853 (buprof12, BU peer-unit descriptions) and PR #854 (berkeleyprof9, Berkeley
structural de-fabrication) each branched off ``budefab1`` and auto-merged on green CI
within minutes, leaving ``main`` with two alembic heads. This empty merge unifies them so
``test_alembic_has_single_head`` passes and Deploy Backend can run. No schema/data changes.

Revision ID: buberkmerge1
Revises: buprof12, berkeleyprof9
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "buberkmerge1"
down_revision = ("buprof12", "berkeleyprof9")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
