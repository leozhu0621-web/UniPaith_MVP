"""Spec 27 — Posts/Events/Promotions: CTAs, visibility, per-object metrics,
event impressions + attendance, promotion target kind.

Chains onto main's single head (``f24da7a0c1b3`` Spec 24 data-upload), keeping a
single linear head (``test_alembic_has_single_head``).

Adds:
- ``institution_posts``: ``click_count``/``save_count``/``request_info_count``/
  ``apply_started_count`` (Spec 27 §5), ``ctas`` (§2.4), ``visibility`` (§2.3).
- ``events``: ``view_count`` (§5 impressions).
- ``event_rsvps``: ``attendance_status`` (§3.1 attended | no_show).
- ``promotions``: ``target_kind`` + ``target_url`` (§4.1).

Every op is guarded with ``_has_column`` so the revision is a safe no-op against a
dev/test DB built from the models via ``create_all``.

Revision ID: f27e5a1c0d34
Revises: f24da7a0c1b3
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f27e5a1c0d34"  # pragma: allowlist secret
down_revision = "f24da7a0c1b3"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        return column in {c["name"] for c in insp.get_columns(table)}
    except Exception:
        return False


def _add(table: str, column: sa.Column) -> None:
    if not _has_column(table, column.name):
        op.add_column(table, column)


def _drop(table: str, column: str) -> None:
    if _has_column(table, column):
        op.drop_column(table, column)


def upgrade() -> None:
    # institution_posts — engagement counters + CTAs + visibility scope
    _add(
        "institution_posts",
        sa.Column("click_count", sa.Integer(), server_default="0", nullable=False),
    )
    _add(
        "institution_posts",
        sa.Column("save_count", sa.Integer(), server_default="0", nullable=False),
    )
    _add(
        "institution_posts",
        sa.Column("request_info_count", sa.Integer(), server_default="0", nullable=False),
    )
    _add(
        "institution_posts",
        sa.Column("apply_started_count", sa.Integer(), server_default="0", nullable=False),
    )
    _add(
        "institution_posts",
        sa.Column("ctas", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    _add(
        "institution_posts",
        sa.Column("visibility", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    # events — impression counter
    _add("events", sa.Column("view_count", sa.Integer(), server_default="0", nullable=False))
    # event_rsvps — attendance capture
    _add("event_rsvps", sa.Column("attendance_status", sa.String(length=20), nullable=True))
    # promotions — target kind + custom landing URL
    _add(
        "promotions",
        sa.Column("target_kind", sa.String(length=20), server_default="program", nullable=False),
    )
    _add("promotions", sa.Column("target_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    _drop("promotions", "target_url")
    _drop("promotions", "target_kind")
    _drop("event_rsvps", "attendance_status")
    _drop("events", "view_count")
    _drop("institution_posts", "visibility")
    _drop("institution_posts", "ctas")
    _drop("institution_posts", "apply_started_count")
    _drop("institution_posts", "request_info_count")
    _drop("institution_posts", "save_count")
    _drop("institution_posts", "click_count")
