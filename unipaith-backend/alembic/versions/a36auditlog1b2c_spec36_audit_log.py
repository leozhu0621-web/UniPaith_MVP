"""Spec 36 (Audit Log): complete the append-only audit substrate.

Additive only. Extends ``admissions_audit_log`` so it carries the full Spec 36
§3 ``AuditEvent`` shape, hardens it as append-only, and backfills the new
taxonomy onto legacy rows.

1. **New columns** on ``admissions_audit_log``:
   - ``category`` — the §2 13-category bucket (nullable; inferred from
     ``action`` on write, backfilled here for legacy rows).
   - ``actor_role`` — student | institution_admin | system | ai_agent.
   - ``reason`` — override rationale (§3; required for overrides at the
     service layer, not the column).
   - ``ip_address`` / ``user_agent`` — request provenance.
2. **``institution_id`` made nullable** (§3 — ``string | null``) so
   student-scoped events (consent / export / deletion) need no institution.
3. **Indexes** for category-scoped listing + actor filtering.
4. **Backfill** ``category`` + ``actor_role`` from existing ``action`` values.
5. **Append-only trigger** (§11) — a ``BEFORE UPDATE OR DELETE`` trigger that
   raises, so rows can never be mutated or removed. PostgreSQL only.

Chains off ``d33a1b2c4e5f`` (the Spec 33 head) to keep a single linear head
(``test_alembic_has_single_head``). All operations are guarded so the revision
is a safe no-op against a dev/test DB built from the models via ``create_all``.

Revision ID: a36auditlog1b2c
Revises: d33a1b2c4e5f
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op
from unipaith.models.audit import (
    AUDIT_APPEND_ONLY_DROP_SQL,
    AUDIT_APPEND_ONLY_INSTALL_SQL,
)

# revision identifiers, used by Alembic.
revision = "a36auditlog1b2c"  # pragma: allowlist secret
down_revision = "d33a1b2c4e5f"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_TABLE = "admissions_audit_log"


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {c["name"] for c in _inspector().get_columns(table)}


def _has_index(table: str, name: str) -> bool:
    if not _has_table(table):
        return False
    return name in {ix["name"] for ix in _inspector().get_indexes(table)}


def _is_pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _has_table(_TABLE):
        # Fresh create_all DB without the table yet — nothing to extend.
        return

    # ── 1. new columns ──────────────────────────────────────────────────────
    if not _has_column(_TABLE, "category"):
        op.add_column(_TABLE, sa.Column("category", sa.String(length=40), nullable=True))
    if not _has_column(_TABLE, "actor_role"):
        op.add_column(_TABLE, sa.Column("actor_role", sa.String(length=20), nullable=True))
    if not _has_column(_TABLE, "reason"):
        op.add_column(_TABLE, sa.Column("reason", sa.Text(), nullable=True))
    if not _has_column(_TABLE, "ip_address"):
        op.add_column(_TABLE, sa.Column("ip_address", sa.String(length=45), nullable=True))
    if not _has_column(_TABLE, "user_agent"):
        op.add_column(_TABLE, sa.Column("user_agent", sa.Text(), nullable=True))

    # ── 2. institution_id → nullable (Spec 36 §3) ───────────────────────────
    # PG only; on create_all DBs the model already declares it nullable.
    if _is_pg():
        op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN institution_id DROP NOT NULL")

    # ── 3. indexes ──────────────────────────────────────────────────────────
    if not _has_index(_TABLE, "ix_audit_inst_category_created"):
        op.create_index(
            "ix_audit_inst_category_created",
            _TABLE,
            ["institution_id", "category", "created_at"],
        )
    if not _has_index(_TABLE, "ix_audit_actor"):
        op.create_index("ix_audit_actor", _TABLE, ["actor_user_id"])

    # ── 4. backfill category + actor_role on legacy rows ─────────────────────
    op.execute(
        f"""
        UPDATE {_TABLE} SET category = CASE
            WHEN action IN ('status_change','submitted') THEN 'status_change'
            WHEN action IN ('decision_release','decision_outcome') THEN 'decision_release'
            WHEN action IN ('reviewer_assigned','reviewer_removed') THEN 'reviewer_assigned'
            WHEN action LIKE 'checklist%' THEN 'checklist_change'
            WHEN action LIKE 'dataset%' OR action LIKE 'document%' THEN 'document_replaced'
            WHEN action LIKE 'waiver%' THEN 'waiver_override'
            WHEN action LIKE 'batch_%' THEN 'batch_action'
            WHEN action IN ('integrity_signal_resolved','ignore')
                 OR action LIKE 'integrity%' THEN 'integrity_resolution'
            WHEN action LIKE 'ai_generated%' OR action LIKE 'ai_artifact%' THEN 'ai_generated'
            WHEN action LIKE 'consent%' THEN 'consent_change'
            WHEN action = 'data_export' THEN 'data_export'
            WHEN action LIKE 'data_deletion%'
                 OR action LIKE 'account_deletion%' THEN 'data_deletion'
            WHEN action LIKE 'fairness%' THEN 'fairness_signal_override'
            WHEN action LIKE 'inbox.%' THEN 'message'
            WHEN action LIKE 'team%' THEN 'team_invite'
            WHEN action = 'blind_review_reveal' THEN 'review'
            ELSE 'other'
        END
        WHERE category IS NULL
        """
    )
    op.execute(
        f"""
        UPDATE {_TABLE}
           SET actor_role = CASE WHEN actor_user_id IS NULL
                                 THEN 'system' ELSE 'institution_admin' END
         WHERE actor_role IS NULL
        """
    )

    # ── 5. append-only enforcement (Spec 36 §11) ─────────────────────────────
    if _is_pg():
        for stmt in AUDIT_APPEND_ONLY_INSTALL_SQL:
            op.execute(stmt)


def downgrade() -> None:
    if not _has_table(_TABLE):
        return

    if _is_pg():
        for stmt in AUDIT_APPEND_ONLY_DROP_SQL:
            op.execute(stmt)

    for ix in ("ix_audit_actor", "ix_audit_inst_category_created"):
        if _has_index(_TABLE, ix):
            op.drop_index(ix, table_name=_TABLE)

    for col in ("user_agent", "ip_address", "reason", "actor_role", "category"):
        if _has_column(_TABLE, col):
            op.drop_column(_TABLE, col)

    # Restore NOT NULL on institution_id (PG only; best-effort).
    if _is_pg():
        op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN institution_id SET NOT NULL")
