"""Spec 44 — Adaptive Intake Engine (four-layer signal pipeline).

Adds the engine storage: ``raw_inputs`` (immutable raw layer), ``student_signals``
(normalized canonical layer carrying the Spec 42 ``SignalRecordMixin`` provenance
envelope), ``signal_change_events`` (append-only audit ledger, §9.6), and
``signal_clarifications`` (low-confidence confirm/correct queue, §6).

No new AI agent — the engine reuses ``DiscoveryExtractor`` + ``DocumentParseTriage``
— so the ``ck_ai_turns_agent`` vocabulary is untouched.

Every table create is guarded (``_has_table``) so the migration is a safe no-op
against a dev/test DB built from the models via ``create_all`` (conftest path).

Revision ID: s44a1b2c3d4e
Revises: m43a1b2c3d4e
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s44a1b2c3d4e"  # pragma: allowlist secret
# Rebased onto origin/main after Spec 43 (#245) merged ahead of this branch; its
# migration m43a1b2c3d4e chained off p42a1b2c3d4e and is now the single head, so
# chain off it to keep the graph single-headed (test_alembic_has_single_head).
# Spec 44 adds no AI agent, so the ck_ai_turns_agent vocabulary is untouched.
down_revision = "m43a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


_SOURCE_CHECK = (
    "source IN ('student-typed','student-uploaded','student-link','student-derived',"
    "'institution-supplied','system-derived','system-extracted','third-party-verified')"
)
_CHANNEL_CHECK = (
    "channel IN ('discovery_chat','form','document','external_link','institution','system')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _student_fk() -> sa.Column:
    return sa.Column(
        "student_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )


def upgrade() -> None:
    # ── 1. raw_inputs (immutable raw layer) ──────────────────────────────────
    if not _has_table("raw_inputs"):
        op.create_table(
            "raw_inputs",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            _student_fk(),
            sa.Column("channel", sa.String(20), nullable=False),
            sa.Column("signal_name", sa.String(80), nullable=True),
            sa.Column("raw_value", postgresql.JSONB(), nullable=True),
            sa.Column("source", sa.String(32), nullable=False, server_default="student-typed"),
            sa.Column("raw_input_ref", sa.String(255), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(_CHANNEL_CHECK, name="ck_raw_inputs_channel"),
            sa.CheckConstraint(_SOURCE_CHECK, name="ck_raw_inputs_source"),
        )
        op.create_index("ix_raw_inputs_student_created", "raw_inputs", ["student_id", "created_at"])
        op.create_index("ix_raw_inputs_student_signal", "raw_inputs", ["student_id", "signal_name"])

    # ── 2. student_signals (normalized canonical layer) ──────────────────────
    if not _has_table("student_signals"):
        op.create_table(
            "student_signals",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            _student_fk(),
            sa.Column("signal_name", sa.String(80), nullable=False),
            sa.Column("category", sa.String(40), nullable=False, server_default="other"),
            sa.Column("value", postgresql.JSONB(), nullable=True),
            # SignalRecordMixin (§5).
            sa.Column("source", sa.String(32), nullable=False, server_default="student-typed"),
            sa.Column("confidence", sa.Integer(), nullable=False, server_default="70"),
            sa.Column("value_normalized", postgresql.JSONB(), nullable=True),
            sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("raw_input_ref", sa.String(255), nullable=True),
            sa.Column(
                "provenance_chain",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
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
            sa.UniqueConstraint(
                "student_id", "signal_name", name="uq_student_signals_student_signal"
            ),
            sa.CheckConstraint(_SOURCE_CHECK, name="ck_student_signals_source"),
            sa.CheckConstraint(
                "confidence >= 0 AND confidence <= 100",
                name="ck_student_signals_confidence_range",
            ),
        )
        op.create_index("ix_student_signals_student", "student_signals", ["student_id"])
        op.create_index(
            "ix_student_signals_student_category",
            "student_signals",
            ["student_id", "category"],
        )

    # ── 3. signal_change_events (append-only audit ledger §9.6) ──────────────
    if not _has_table("signal_change_events"):
        op.create_table(
            "signal_change_events",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            _student_fk(),
            sa.Column("signal_name", sa.String(80), nullable=False),
            sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source", sa.String(32), nullable=False),
            sa.Column("confidence", sa.Integer(), nullable=False, server_default="70"),
            sa.Column("channel", sa.String(20), nullable=False),
            sa.Column("event", sa.String(20), nullable=False, server_default="updated"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(_CHANNEL_CHECK, name="ck_signal_change_events_channel"),
        )
        op.create_index(
            "ix_signal_change_events_student_created",
            "signal_change_events",
            ["student_id", "created_at"],
        )
        op.create_index(
            "ix_signal_change_events_student_signal",
            "signal_change_events",
            ["student_id", "signal_name"],
        )

    # ── 4. signal_clarifications (low-confidence confirm/correct queue §6) ────
    if not _has_table("signal_clarifications"):
        op.create_table(
            "signal_clarifications",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            _student_fk(),
            sa.Column("signal_name", sa.String(80), nullable=False),
            sa.Column("raw_value", postgresql.JSONB(), nullable=True),
            sa.Column("suggested_value", postgresql.JSONB(), nullable=True),
            sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("status", sa.String(12), nullable=False, server_default="open"),
            sa.Column("resolved_value", postgresql.JSONB(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.CheckConstraint(
                "status IN ('open','confirmed','corrected')",
                name="ck_signal_clarifications_status",
            ),
        )
        op.create_index(
            "uq_signal_clarifications_one_open",
            "signal_clarifications",
            ["student_id", "signal_name"],
            unique=True,
            postgresql_where=sa.text("status = 'open'"),
        )
        op.create_index(
            "ix_signal_clarifications_student_status",
            "signal_clarifications",
            ["student_id", "status"],
        )


def downgrade() -> None:
    for table in (
        "signal_clarifications",
        "signal_change_events",
        "student_signals",
        "raw_inputs",
    ):
        if _has_table(table):
            op.drop_table(table)
