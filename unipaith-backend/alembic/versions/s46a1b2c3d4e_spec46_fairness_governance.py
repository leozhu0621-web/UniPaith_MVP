"""Spec 46 — Data Rights, Privacy & Fairness Governance.

Adds the fairness auto-halt ledger: ``fairness_signals`` (one row per program ×
intake × protected_attribute × week — the disparate-impact reading + severity)
and ``fairness_overrides`` (an institution admin's logged decision to lift a
halt, §6.3). Extends ``programs`` with the halt state: ``matching_halted``,
``fairness_override_active``, ``override_expires_at``, ``fairness_threshold``.

No new AI agent — fairness is deterministic math — so the ``ck_ai_turns_agent``
vocabulary is untouched.

Every create/add is guarded so the migration is a safe no-op against a dev/test
DB built from the models via ``create_all`` (conftest path).

Revision ID: s46a1b2c3d4e
Revises: s44a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s46a1b2c3d4e"  # pragma: allowlist secret
# Chains off Spec 44 (the single head at branch time). Spec 46 adds no AI agent.
down_revision = "s44a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


_ATTR_CHECK = (
    "protected_attribute IN ('race','gender','first_gen','international',"
    "'nationality_region','disability','veteran')"
)
_SEVERITY_CHECK = "severity IN ('info','warning','high','auto_halt','override_active')"


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    # ── 0. institutions data-governance config (§9) ──────────────────────────
    if not _has_column("institutions", "data_governance"):
        op.add_column(
            "institutions",
            sa.Column("data_governance", postgresql.JSONB(), nullable=True),
        )

    # ── 1. programs halt columns (§6.2 / §9) ─────────────────────────────────
    if not _has_column("programs", "matching_halted"):
        op.add_column(
            "programs",
            sa.Column("matching_halted", sa.Boolean(), nullable=False, server_default="false"),
        )
    if not _has_column("programs", "fairness_override_active"):
        op.add_column(
            "programs",
            sa.Column(
                "fairness_override_active",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
        )
    if not _has_column("programs", "override_expires_at"):
        op.add_column(
            "programs",
            sa.Column("override_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _has_column("programs", "fairness_threshold"):
        op.add_column(
            "programs",
            sa.Column(
                "fairness_threshold",
                sa.Numeric(3, 2),
                nullable=False,
                server_default="0.20",
            ),
        )

    # ── 2. fairness_signals (§6.5) ───────────────────────────────────────────
    if not _has_table("fairness_signals"):
        op.create_table(
            "fairness_signals",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "program_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("programs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "intake_round_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("intake_rounds.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("week_start", sa.Date(), nullable=False),
            sa.Column("protected_attribute", sa.String(30), nullable=False),
            sa.Column("cohort_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("di_ratio", sa.Numeric(6, 4), nullable=True),
            sa.Column("delta", sa.Numeric(6, 4), nullable=True),
            sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
            sa.Column("sample_sufficient", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(_ATTR_CHECK, name="ck_fairness_signals_attribute"),
            sa.CheckConstraint(_SEVERITY_CHECK, name="ck_fairness_signals_severity"),
        )
        op.create_index(
            "ix_fairness_signals_cohort_week",
            "fairness_signals",
            ["program_id", "intake_round_id", "protected_attribute", "week_start"],
        )
        op.create_index(
            "ix_fairness_signals_program_week",
            "fairness_signals",
            ["program_id", "week_start"],
        )

    # ── 3. fairness_overrides (§6.3) ─────────────────────────────────────────
    if not _has_table("fairness_overrides"):
        op.create_table(
            "fairness_overrides",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column(
                "fairness_signal_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("fairness_signals.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "institution_admin_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("rationale", sa.Text(), nullable=False),
            sa.Column("override_expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_fairness_overrides_signal", "fairness_overrides", ["fairness_signal_id"]
        )


def downgrade() -> None:
    if _has_table("fairness_overrides"):
        op.drop_table("fairness_overrides")
    if _has_table("fairness_signals"):
        op.drop_table("fairness_signals")
    for col in (
        "fairness_threshold",
        "override_expires_at",
        "fairness_override_active",
        "matching_halted",
    ):
        if _has_column("programs", col):
            op.drop_column("programs", col)
    if _has_column("institutions", "data_governance"):
        op.drop_column("institutions", "data_governance")
