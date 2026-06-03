"""Spec 63 §4/§10 — Qwen provider (the ML backend transport).

Qwen is the platform's **invisible ML backend** — it processes, scores and
synthesizes informational content but **never serves a human-facing agent** (the
hard boundary in ``ai/boundary.py`` enforces that on every resolution). This
provider registers Qwen as a backend transport so processing agents (extractor,
validator, query-interpreter, document-triage, authenticity, segment-builder,
…) can be routed to it via ``ai_provider_per_agent_json`` once eval (`62`)
promotes it.

Transport
---------
Qwen is served by **vLLM** (continuous batching, §10) or **Bedrock**, both of
which expose an **OpenAI-compatible ``/v1``**. So this provider subclasses
``OpenAIProvider`` to reuse its proven Anthropic-shape ↔ OpenAI-chat translation
(content blocks, forced tool-use, tool_choice) verbatim — it overrides only the
endpoint (a separate ``qwen_base_url``), the tier→model map (Qwen instruct
sizes), availability (gated on ``qwen_enabled``), and pricing.

Cost
----
Self-hosted Qwen has no per-token API price — the real cost is amortized
GPU-hours, tracked separately in §14. The per-MTok numbers below are a
conservative *amortized* estimate so the ``ai_turns`` ledger and the cost
dashboard show a non-zero, clearly-cheap figure rather than ``None``.

Fallback
--------
The provider is off the human-facing critical path by construction, so a Qwen
outage degrades *processing* only — the AIClient's failover order
(``ai_provider_failover_csv``) routes the next attempt to Anthropic, and the
Claude conversation is never affected (§10/§16).
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.ai.providers.base import Tier
from unipaith.ai.providers.openai_provider import OpenAIProvider
from unipaith.config import settings

# Per-MTok prices (USD) — conservative *amortized self-host* estimates, far
# below the premium-API tiers (the whole point of §8: cheap at volume). Update
# from the GPU cost model (§14) when the fleet is sized.
_QWEN_PRICES: dict[str, dict[str, float]] = {
    "qwen3-32b-instruct": {"input": 0.20, "output": 0.20},
    "qwen3-14b-instruct": {"input": 0.10, "output": 0.10},
    "qwen3-7b-instruct": {"input": 0.05, "output": 0.05},
    "qwen3-embedding-8b": {"input": 0.01, "output": 0.0},
}


class QwenProvider(OpenAIProvider):
    """Concrete provider for the self-hosted Qwen ML backend. OpenAI-compatible
    transport, separate endpoint, never serves a human-facing agent."""

    name = "qwen"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        max_retries: int = 2,
    ):
        self.base_url = base_url if base_url is not None else settings.qwen_base_url
        # vLLM accepts any non-empty token; default to a sentinel so the parent's
        # empty-key guard never trips for a keyless self-host.
        self.api_key = api_key if api_key is not None else (settings.qwen_api_key or "EMPTY")
        self.max_retries = max_retries
        self._sdk = None

    def is_available(self) -> bool:
        # Registered but inert until explicitly enabled per-env (§11): Qwen is a
        # transport on the bench, not the default route.
        if not settings.qwen_enabled or not self.base_url:
            return False
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return True

    def model_id(self, tier: Tier) -> str:
        if tier == "flagship":
            return settings.qwen_model_flagship
        if tier == "batch":
            return settings.qwen_model_batch
        return settings.qwen_model_workhorse

    def _get_sdk(self):
        if self._sdk is None:
            from openai import AsyncOpenAI

            # Point the OpenAI SDK at the vLLM / Bedrock OpenAI-compatible base.
            self._sdk = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._sdk

    @staticmethod
    def _compute_cost(*, model_id: str, input_tokens: int, output_tokens: int) -> Decimal:
        prices = _QWEN_PRICES.get(model_id)
        if prices is None:
            return Decimal("0")
        cost = (input_tokens / 1_000_000) * prices["input"] + (output_tokens / 1_000_000) * prices[
            "output"
        ]
        return Decimal(str(round(cost, 6)))
