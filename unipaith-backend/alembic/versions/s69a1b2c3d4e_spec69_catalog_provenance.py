"""Spec 69 — Program Catalog Ingestion: provenance/freshness columns.

Adds catalog-ingestion provenance + freshness + stable-identity columns to
``programs`` and ``schools`` (§6): ``catalog_source``, ``source_url``,
``external_id``, ``slug``, ``cip_code`` (programs), ``last_ingested_at``,
``field_provenance``. Net-additive + nullable — a hand-created or self-served
row leaves them null; an ingested row carries source + per-field provenance so a
catalog fact can answer "sourced from <domain>, updated N days ago" (60 §4).
``slug``/``external_id`` give a stable identity for idempotent re-crawl + SEO.

Every add is guarded (``_has_column`` / ``_has_index``) so the migration is a
safe no-op against a dev/test DB built from the models via ``create_all`` (the
conftest path), and runs incrementally in production from the prior head.

Revision ID: s69a1b2c3d4e
Revises: s68a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s69a1b2c3d4e"  # pragma: allowlist secret
down_revision = "s68a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None

# (column, type) — schools get all but cip_code (program grain).
_PROGRAM_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    ("catalog_source", sa.String(24)),
    ("source_url", sa.Text()),
    ("external_id", sa.String(160)),
    ("slug", sa.String(200)),
    ("cip_code", sa.String(12)),
    ("last_ingested_at", sa.DateTime(timezone=True)),
    ("field_provenance", postgresql.JSONB(astext_type=sa.Text())),
]
_SCHOOL_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    (name, typ) for name, typ in _PROGRAM_COLS if name != "cip_code"
]


def _has_column(table: str, col: str) -> bool:
    return col in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    return name in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}


def _add_cols(table: str, cols: list[tuple[str, sa.types.TypeEngine]]) -> None:
    for name, typ in cols:
        if not _has_column(table, name):
            op.add_column(table, sa.Column(name, typ, nullable=True))


def _add_index(table: str, name: str, col: str, unique: bool = False) -> None:
    if not _has_index(table, name):
        op.create_index(name, table, [col], unique=unique)


def upgrade() -> None:
    _add_cols("programs", _PROGRAM_COLS)
    _add_cols("schools", _SCHOOL_COLS)
    _add_index("programs", "ix_programs_slug", "slug", unique=True)
    _add_index("programs", "ix_programs_external_id", "external_id")
    _add_index("schools", "ix_schools_slug", "slug", unique=True)
    _add_index("schools", "ix_schools_external_id", "external_id")


def downgrade() -> None:
    for name in ("ix_schools_external_id", "ix_schools_slug"):
        if _has_index("schools", name):
            op.drop_index(name, table_name="schools")
    for name in ("ix_programs_external_id", "ix_programs_slug"):
        if _has_index("programs", name):
            op.drop_index(name, table_name="programs")
    for name, _typ in _SCHOOL_COLS:
        if _has_column("schools", name):
            op.drop_column("schools", name)
    for name, _typ in _PROGRAM_COLS:
        if _has_column("programs", name):
            op.drop_column("programs", name)
