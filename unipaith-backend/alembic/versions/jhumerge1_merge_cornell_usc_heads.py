"""Merge cornellpercred1 + uscdebris2 heads before JHU per-credential repair.

Revision ID: jhumerge1
Revises: cornellpercred1, uscdebris2
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "jhumerge1"
down_revision = ("cornellpercred1", "uscdebris2")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
