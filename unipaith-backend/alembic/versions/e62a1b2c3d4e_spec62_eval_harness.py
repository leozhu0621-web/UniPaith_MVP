"""Spec 62 — Evaluation Harness: the two persisted additions.

The shared harness reuses the ``ml_loop`` tables (``evaluation_runs`` etc.) and
the ``ai_turns`` ledger; it adds exactly two tables (§8):

- ``eval_cases``   — the versioned golden set (consumer · case_key · rubric
  version · input · expected · dimensions · source · severity).
- ``eval_results`` — one row per case per run, joined to ``evaluation_runs``.

Every create is guarded (``_has_table``) so the migration is a safe no-op against
a dev/test DB built from the models via ``create_all`` (the conftest path), and
runs incrementally in production from the prior head.

Revision ID: e62a1b2c3d4e
Revises: s63a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e62a1b2c3d4e"  # pragma: allowlist secret
# Re-pointed onto s63a1b2c3d4e (Spec 63 ML core, which also chained off s60) when
# it merged concurrently — chain after it to keep the graph single-headed
# (test_alembic_has_single_head). e62's tables are independent of s63's, so the
# order is purely about a linear history.
down_revision = "s63a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _id() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def _create_eval_cases() -> None:
    if _has_table("eval_cases"):
        return
    op.create_table(
        "eval_cases",
        _id(),
        sa.Column("consumer", sa.String(30), nullable=False),
        sa.Column("case_key", sa.String(120), nullable=False),
        sa.Column("domain", sa.String(60), nullable=True),
        sa.Column(
            "input_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("expected", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rubric_version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("source", sa.String(20), nullable=False, server_default="curated"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="normal"),
        *_timestamps(),
        sa.UniqueConstraint(
            "consumer", "case_key", "rubric_version", name="uq_eval_cases_consumer_key_version"
        ),
    )
    op.create_index("ix_eval_cases_consumer", "eval_cases", ["consumer"])
    op.create_index("ix_eval_cases_source", "eval_cases", ["source"])


def _create_eval_results() -> None:
    if _has_table("eval_results"):
        return
    op.create_table(
        "eval_results",
        _id(),
        sa.Column(
            "evaluation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "eval_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("eval_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("consumer", sa.String(30), nullable=False),
        sa.Column(
            "dimension_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("deterministic_passed", sa.Boolean(), nullable=False),
        sa.Column("judge_model", sa.String(50), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("ix_eval_results_run", "eval_results", ["evaluation_run_id"])
    op.create_index("ix_eval_results_case", "eval_results", ["eval_case_id"])
    op.create_index("ix_eval_results_consumer", "eval_results", ["consumer"])


def upgrade() -> None:
    _create_eval_cases()
    _create_eval_results()


def downgrade() -> None:
    if _has_table("eval_results"):
        op.drop_table("eval_results")
    if _has_table("eval_cases"):
        op.drop_table("eval_cases")
