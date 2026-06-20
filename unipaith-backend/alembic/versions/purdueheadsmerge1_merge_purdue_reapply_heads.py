"""Merge dual Purdue re-apply heads (purdueprof12 + purduereapply1)

Two PRs independently fixed the same root cause — the de-fabricated Purdue catalog
never reached production because ``purduedefab1`` was stamped during the dual-head deploy
failure it raced, so Alembic never re-ran its ``apply()``. #837 shipped ``purdueprof12``
and #840 shipped ``purduereapply1``, both branched off ``purduescholmerge1`` and both
re-running ``purdue_profile.apply()`` (idempotent), leaving ``main`` with two heads. This
empty merge revision unifies them so ``alembic upgrade head`` resolves to a single head
and the deploy is unblocked. No data change.

Revision ID: purdueheadsmerge1
Revises: purdueprof12, purduereapply1
Create Date: 2026-06-19
"""

from __future__ import annotations

revision = "purdueheadsmerge1"
down_revision = ("purdueprof12", "purduereapply1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
