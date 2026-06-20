"""Merge concurrent heads: AI-structure visa migration + UT Austin per-credential repair.

Two migrations landed concurrently on main — ``aivisamerge1`` (visa-feasibility merge) and
``utaustpercrd1`` (UT Austin frame-stripped shared-body repair). No-op merge unifying them
into a single head.

Revision ID: michheadmrg1
Revises: aivisamerge1, utaustpercrd1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "michheadmrg1"
down_revision = ("aivisamerge1", "utaustpercrd1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
