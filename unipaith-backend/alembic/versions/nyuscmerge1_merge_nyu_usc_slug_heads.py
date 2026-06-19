"""Merge dual heads nyuslugfix1 + uscdefab1 (both branched off uscprof4).

Revision ID: nyuscmerge1
Revises: nyuslugfix1, uscdefab1
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "nyuscmerge1"
down_revision = ("nyuslugfix1", "uscdefab1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
