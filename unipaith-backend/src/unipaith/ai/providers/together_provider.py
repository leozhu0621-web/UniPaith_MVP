"""Together provider — Qwen 3 via Together AI (managed, human-facing).

Product decision (2026-06-25): Uni's human-facing conversation runs on **Qwen**,
served by **Together**'s managed OpenAI-compatible API.

This is a SEPARATE transport from the self-hosted `qwen` ML backend
(`ai/providers/qwen_provider.py`). The spec-63 boundary (`ai/boundary.py`) pins
human-facing agents away from the *self-hosted* `qwen` transport (the invisible
ML backend that must never touch a human). `together` is a *managed* transport
that is allowed to serve human-facing agents — so routing the orchestrator and
advisory agents here does not weaken the boundary that protects the self-hosted
Qwen box; it simply moves the conversation off Anthropic and onto Qwen-via-Together.

Subclasses `OpenAIProvider` to reuse its proven Anthropic-shape <-> OpenAI-chat
translation (content blocks, forced tool-use, tool_choice) verbatim — overriding
only the endpoint, the tier->model map, availability, and pricing.
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.ai.providers.base import Tier
from unipaith.ai.providers.openai_provider import OpenAIProvider
from unipaith.config import settings


class TogetherProvider(OpenAIProvider):
    """Qwen 3 on Together (managed, OpenAI-compatible). Available whenever a
    Together key is configured."""

    name = "together"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        max_retries: int = 2,
    ):
        self.base_url = base_url if base_url is not None else settings.together_base_url
        self.api_key = api_key if api_key is not None else settings.together_api_key
        self.max_retries = max_retries
        self._sdk = None

    def is_available(self) -> bool:
        if not self.api_key or not self.base_url:
            return False
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return True

    def model_id(self, tier: Tier) -> str:
        if tier == "flagship":
            return settings.together_model_flagship
        if tier == "batch":
            return settings.together_model_batch
        return settings.together_model_workhorse

    def _get_sdk(self):
        if self._sdk is None:
            from openai import AsyncOpenAI

            self._sdk = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._sdk

    @staticmethod
    def _compute_cost(*, model_id: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Per-MTok USD for the audit ledger. Together's published Qwen rates
        (approx, 2026-06) read from settings at call time so a model swap updates
        pricing without a code change. Unknown model -> 0 (same convention as the
        sibling providers)."""
        rates: dict[str, tuple[float, float]] = {
            settings.together_model_flagship: (0.20, 0.60),
            settings.together_model_workhorse: (0.20, 0.60),
            settings.together_model_batch: (0.10, 0.30),
        }
        pair = rates.get(model_id)
        if pair is None:
            return Decimal("0")
        in_rate, out_rate = pair
        cost = (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
        return Decimal(str(round(cost, 6)))
