"""Merge deep intelligence and NYU/reference heads.

``deepintelmerge1`` landed the profile-intelligence work while ``nyurefmrg1`` landed
afterward to merge NYU gold repair and reference-institution heads. This empty
merge restores a single Alembic head for backend deployment.

Revision ID: deepnyurefmrg1
Revises: deepintelmerge1, nyurefmrg1
Create Date: 2026-06-21
"""

from __future__ import annotations

revision = "deepnyurefmrg1"
down_revision = ("deepintelmerge1", "nyurefmrg1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
