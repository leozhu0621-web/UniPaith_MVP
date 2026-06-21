"""Merge concurrent heads: colaivisamerge1 + michaimrg1.

PR #953 (Michigan per-credential repair) chained ``michpercrd1`` off
``columbiapercred1`` while #951 had already merged ``columbiapercred1`` with
``aivisamerge1`` into ``colaivisamerge1``. The follow-on ``michaimrg1`` merge left
``main`` with two heads and blocked Deploy Backend. This no-op merge unifies them.

Revision ID: colmichmerge1
Revises: colaivisamerge1, michaimrg1
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "colmichmerge1"
down_revision = ("colaivisamerge1", "michaimrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
