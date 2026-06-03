"""Spec 63 — register the Qwen ML backend as an audited provider transport.

Spec 63 makes Qwen the platform's invisible ML backend (embeddings, extraction,
normalization, classification, L3 scoring, display synthesis). Every model call
already writes its transport to ``ai_turns.provider`` (spec 03 §8). This migration
widens the ``ck_ai_turns_provider`` CHECK so Qwen-served processing calls validate
— which is also the **auditable proof** of the §1 boundary: a human-facing agent's
row can only ever carry ``anthropic``/``openai`` (``ai/boundary.py`` pins it), so a
``provider='qwen'`` row is, by construction, never a human-facing surface.

Drop + recreate as two separate statements (asyncpg rejects a multi-statement
``op.execute``). Idempotent: ``DROP ... IF EXISTS`` then ``ADD`` — safe whether the
table was built from the prior migration head (prod) or from the models via
``create_all`` (the conftest test path already carries the widened constraint).

Revision ID: s63a1b2c3d4e
Revises: s60a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "s63a1b2c3d4e"  # pragma: allowlist secret
down_revision = "s60a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


_WITH_QWEN = "provider IN ('anthropic','openai','bedrock','qwen','rule_based')"
_WITHOUT_QWEN = "provider IN ('anthropic','openai','bedrock','rule_based')"


def upgrade() -> None:
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_provider")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_provider CHECK ({_WITH_QWEN})")


def downgrade() -> None:
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_provider")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_provider CHECK ({_WITHOUT_QWEN})")
