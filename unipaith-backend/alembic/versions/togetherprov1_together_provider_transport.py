"""Together (managed Qwen) — register as an audited provider transport.

2026-06-25: Uni's conversation AND the ML/extraction agents moved to Qwen via
Together (managed, OpenAI-compatible, serverless). Every model call writes its
transport to ``ai_turns.provider`` (spec 03 §8), so the ``ck_ai_turns_provider``
CHECK must accept ``'together'`` — otherwise the turn-log INSERT raises a
CheckViolation and the whole turn fails, silently degrading Uni to limited
rule-based mode. Widen the CHECK to include ``'together'`` alongside the existing
transports.

Drop + recreate as two separate statements (asyncpg rejects a multi-statement
``op.execute``). Idempotent: ``DROP ... IF EXISTS`` then ``ADD`` — safe whether the
table was built from a prior migration head (prod) or from the models via
``create_all`` (conftest already carries the widened constraint). Mirrors
``s63a1b2c3d4e_spec63_qwen_provider``.

Revision ID: togetherprov1
Revises: washuprof1
Create Date: 2026-06-26

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "togetherprov1"  # pragma: allowlist secret
down_revision = "washuprof1"  # pragma: allowlist secret
branch_labels = None
depends_on = None


_WITH_TOGETHER = "provider IN ('anthropic','openai','bedrock','qwen','rule_based','together')"
_WITHOUT_TOGETHER = "provider IN ('anthropic','openai','bedrock','qwen','rule_based')"


def upgrade() -> None:
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_provider")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_provider CHECK ({_WITH_TOGETHER})")


def downgrade() -> None:
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_provider")
    op.execute(
        f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_provider CHECK ({_WITHOUT_TOGETHER})"
    )
