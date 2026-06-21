"""Merge concurrent heads: AI-structure visa merge + Michigan per-credential repair.

``aivisamerge1`` (visa-feasibility column merge) and ``michpercrd1`` (Michigan
frame-stripped shared-body repair) landed on parallel branches. No-op merge.

Revision ID: michaimrg1
Revises: aivisamerge1, michpercrd1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "michaimrg1"
down_revision = ("aivisamerge1", "michpercrd1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
