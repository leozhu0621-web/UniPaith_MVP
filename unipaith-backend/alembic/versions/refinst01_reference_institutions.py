"""Reference institutions (College Scorecard) — ref_institutions table.

Adds the typed ``ref_institutions`` reference table (spec 2026-06-20), joining the
Spec 60 ``ref_*`` family. The table is guarded by ``_has_table`` so this is a safe
no-op against a dev/test DB built from the models via ``create_all`` (the conftest
path) and runs incrementally in production.

Chains off ``colmichmrg1`` (the current single head after merging origin/main, which
unified the columbia/aivisa/michigan/ut-austin chains) so history stays single-headed
(``test_alembic_has_single_head``).

Revision ID: refinst01institutions
Revises: colmichmrg1
Create Date: 2026-06-20

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "refinst01institutions"  # pragma: allowlist secret
down_revision = "colmichmrg1"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_SOURCE_CHECK = "source IN ('seed','crawled','corroborated','first_party','institution_verified')"
_STATUS_CHECK = "status IN ('provisional','live','review','superseded','archived')"


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table("ref_institutions"):
        return
    op.create_table(
        "ref_institutions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("unitid", sa.Integer(), nullable=False),
        sa.Column("opeid", sa.String(20), nullable=True),
        sa.Column("opeid6", sa.String(20), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("alias", sa.Text(), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("state", sa.String(10), nullable=True),
        sa.Column("zip", sa.String(20), nullable=True),
        sa.Column("lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("lon", sa.Numeric(9, 6), nullable=True),
        sa.Column("control_code", sa.Integer(), nullable=True),
        sa.Column("control", sa.String(40), nullable=True),
        sa.Column("locale_code", sa.Integer(), nullable=True),
        sa.Column("region_code", sa.Integer(), nullable=True),
        sa.Column("pred_degree", sa.Integer(), nullable=True),
        sa.Column("high_degree", sa.Integer(), nullable=True),
        sa.Column("accreditor", sa.String(255), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("price_calc_url", sa.String(500), nullable=True),
        sa.Column("admit_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("sat_avg", sa.Integer(), nullable=True),
        sa.Column("act_mid", sa.Integer(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("cost_attendance", sa.Integer(), nullable=True),
        sa.Column("tuition_in", sa.Integer(), nullable=True),
        sa.Column("tuition_out", sa.Integer(), nullable=True),
        sa.Column("pct_pell", sa.Numeric(6, 4), nullable=True),
        sa.Column("completion_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("retention", sa.Numeric(6, 4), nullable=True),
        sa.Column("earnings_10yr_median", sa.Integer(), nullable=True),
        sa.Column("median_debt", sa.Integer(), nullable=True),
        sa.Column("carnegie_basic", sa.Integer(), nullable=True),
        sa.Column("program_pct", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_vintage", sa.String(40), nullable=True),
        # ProvenanceMixin (Spec 60 §4)
        sa.Column("source", sa.String(24), nullable=False, server_default="crawled"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_domain", sa.String(255), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="provisional"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("unitid", name="uq_ref_institutions_unitid"),
        sa.CheckConstraint(_SOURCE_CHECK, name="ck_ref_institutions_source"),
        sa.CheckConstraint(_STATUS_CHECK, name="ck_ref_institutions_status"),
    )
    op.create_index("ix_ref_institutions_name", "ref_institutions", ["name"])
    op.create_index("ix_ref_institutions_state", "ref_institutions", ["state"])
    op.create_index("ix_ref_institutions_control_code", "ref_institutions", ["control_code"])


def downgrade() -> None:
    if _has_table("ref_institutions"):
        op.drop_table("ref_institutions")
