"""Open-weight provider — Qwen served via Together AI's OpenAI-compatible API.

The migration target (see ``OPEN_MODEL_MIGRATION_PLAN.md`` /
``CLAUDE_CODE_TASK_qwen_migration.md``): make Qwen the single LLM provider for
every agent, with the rule-based path as the only safety net.

Architecture invariant (Spec 03 §1/§5): **swap providers, not call sites.** This
provider subclasses :class:`OpenAIProvider` and reuses its Anthropic↔OpenAI tool
translation wholesale — the forced-tool agents (rationale, strategy,
review_summarizer, authenticity, …) keep producing structured ``tool_use`` blocks
because Together exposes the same OpenAI function-calling surface. Only the
identity, transport (base_url + key), tier→model map, and pricing differ.

Rollout: this provider is built + registered + tested, but the default stays
``anthropic`` (see ``config.py``) until ``OPENSOURCE_API_KEY`` is wired in the
deploy environment. The cutover is then a pure env change
(``AI_PROVIDER_DEFAULT=opensource``, ``AI_PROVIDER_FAILOVER_CSV=opensource``),
reversible without a Claude key.
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.ai.providers.base import Tier
from unipaith.ai.providers.openai_provider import OpenAIProvider
from unipaith.config import settings

# Per-MTok prices (USD) for the Together-served Qwen tiers. Update from Together's
# published rates; an unknown model id costs 0 (the ledger records tokens either
# way, so cost is never blocking).
_OPENSOURCE_PRICES: dict[str, dict[str, float]] = {
    "Qwen/Qwen3-235B-A22B-Instruct": {"input": 0.60, "output": 0.60},
    "Qwen/Qwen3-30B-A3B-Instruct": {"input": 0.20, "output": 0.60},
    "Qwen/Qwen3-8B": {"input": 0.06, "output": 0.20},
}


class OpenSourceProvider(OpenAIProvider):
    """Qwen via Together AI. The default provider once the key is wired.

    Inherits ``chat()``, ``is_available()`` (key + ``openai`` SDK present), and the
    OpenAI tool translation from :class:`OpenAIProvider`. Overrides only what is
    transport-specific: name, init (Together base_url + key), the tier→Qwen model
    map, the SDK builder (so it points at Together), and pricing.
    """

    name = "opensource"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        max_retries: int = 2,
    ):
        self.api_key = api_key if api_key is not None else settings.opensource_api_key
        self.base_url = base_url if base_url is not None else settings.opensource_base_url
        self.max_retries = max_retries
        self._sdk = None

    def model_id(self, tier: Tier) -> str:
        if tier == "flagship":
            return settings.opensource_flagship
        if tier == "batch":
            return settings.opensource_batch
        return settings.opensource_workhorse

    def _get_sdk(self):
        if self._sdk is None:
            from openai import AsyncOpenAI

            self._sdk = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._sdk

    @staticmethod
    def _compute_cost(*, model_id: str, input_tokens: int, output_tokens: int) -> Decimal:
        prices = _OPENSOURCE_PRICES.get(model_id)
        if prices is None:
            return Decimal("0")
        cost = (input_tokens / 1_000_000) * prices["input"] + (output_tokens / 1_000_000) * prices[
            "output"
        ]
        return Decimal(str(round(cost, 6)))
