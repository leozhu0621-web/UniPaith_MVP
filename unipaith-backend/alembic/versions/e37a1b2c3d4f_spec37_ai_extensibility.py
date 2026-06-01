"""Spec 37 (AI Extensibility): per-institution AI configuration.

This revision is additive only:

1. **Adds ``institutions.ai_config`` (JSONB, nullable)** — the per-institution
   AI control surface (Spec 37 §5 / 46 §9):
     {
       "surfaces": {
         "<surface>": {"enabled": bool, "min_confidence": 0-100},
         ...
       },
       "no_training": bool   # 46 §9 no-training tier override
     }
   NULL means "all defaults" (every surface enabled, default thresholds,
   no_training off) — see ``services/ai_config_service.DEFAULT_AI_CONFIG``.

No new AI agent is introduced (``authenticity_risk`` / ``document_parse_triage``
/ ``review_assistant`` are already in ``ck_ai_turns_agent``), so the agent CHECK
is untouched. The human<->AI edit-diff capture (Spec 37 §3) reuses the existing
``admissions_audit_log`` (``old_value`` / ``new_value`` / ``metadata_json``) — no
schema change needed there.

Chains off ``t35a1b2c3d4e`` (the Spec 35 enrollment-yield head, which itself
chains off the Spec 33 head) so the graph stays a single linear head
(``test_alembic_has_single_head``). The column add is guarded with
``_has_column`` so the revision is a safe no-op against a dev/test DB built from
the models via ``create_all``.

Revision ID: e37a1b2c3d4f
Revises: t35a1b2c3d4e
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e37a1b2c3d4f"  # pragma: allowlist secret
down_revision = "t35a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {c["name"] for c in _inspector().get_columns(table)}


def upgrade() -> None:
    if _has_table("institutions") and not _has_column("institutions", "ai_config"):
        op.add_column(
            "institutions",
            sa.Column("ai_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    if _has_column("institutions", "ai_config"):
        op.drop_column("institutions", "ai_config")
