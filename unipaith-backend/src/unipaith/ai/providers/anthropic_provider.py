"""Spec 03 §5 — Anthropic provider implementation.

Wraps the Anthropic SDK behind the AIProvider Protocol. This is the
default + spec-preferred provider; OpenAI is failover.

Notes
-----
- Tier → model resolution reads from `settings` so prod can roll a tier
  forward without a code deploy (spec 03 §6 "Secret update + task
  restart").
- Prompt-cache layout is the caller's responsibility — this provider
  forwards `cache_control` markers and the `anthropic-beta` header so
  the cached system + persona blocks bill at the cached rate.
- Cost is computed here so the AIClient ledger row gets the
  Anthropic-specific cache_read / cache_write multiplier correctly.
"""

from __future__ import annotations

import asyncio
import logging
import time
from decimal import Decimal
from typing import Any

from unipaith.ai.providers.base import (
    AIProvider,
    ChatRequest,
    ChatResponse,
    ProviderTimeoutError,
    ProviderUnavailableError,
    Tier,
)
from unipaith.config import settings

logger = logging.getLogger(__name__)


# Per-MTok prices (USD). Mirrors AIClient.MODEL_PRICES — kept in sync
# manually because the SDK doesn't expose them. Source: spec 03 §10.
_ANTHROPIC_PRICES: dict[str, dict[str, float]] = {
    "claude-opus-4-8": {"input": 15.00, "output": 75.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
}

_CACHE_READ_MULTIPLIER = 0.1
_CACHE_WRITE_MULTIPLIER = 1.25


class AnthropicProvider(AIProvider):
    """Concrete provider for Claude. The flagship/workhorse/batch tier
    map is settings-driven so model upgrades roll forward via env only.
    """

    name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        flagship_model: str | None = None,
        workhorse_model: str | None = None,
        batch_model: str | None = None,
        max_retries: int = 3,
    ):
        self.api_key = api_key if api_key is not None else settings.anthropic_api_key
        self.flagship_model = (
            flagship_model if flagship_model is not None else settings.anthropic_default_flagship
        )
        self.workhorse_model = (
            workhorse_model if workhorse_model is not None else settings.anthropic_default_workhorse
        )
        self.batch_model = (
            batch_model if batch_model is not None else settings.anthropic_default_batch
        )
        self.max_retries = max_retries
        self._sdk = None

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def model_id(self, tier: Tier) -> str:
        if tier == "flagship":
            return self.flagship_model
        if tier == "batch":
            return self.batch_model
        return self.workhorse_model

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self.api_key:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is empty")
        anthropic_sdk = self._get_sdk()
        model_id = self.model_id(request.tier)

        params: dict[str, Any] = {
            "model": model_id,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system,
            "messages": request.messages,
        }
        if request.tools:
            params["tools"] = request.tools
        if request.tool_choice:
            params["tool_choice"] = request.tool_choice

        # Beta header opts the request into prompt caching — the
        # cache_control markers were already set by the caller per
        # spec §3.
        extra_headers = {"anthropic-beta": "prompt-caching-2024-07-31"}

        timeout_s = request.timeout_ms / 1000.0
        start = time.perf_counter()
        last_err: Exception | None = None
        raw_resp: Any | None = None
        for attempt in range(self.max_retries):
            try:
                raw_resp = await anthropic_sdk.messages.create(
                    **params,
                    extra_headers=extra_headers,
                    timeout=timeout_s,
                )
                break
            except TimeoutError as e:
                raise ProviderTimeoutError(f"anthropic timeout after {request.timeout_ms}ms") from e
            except Exception as e:  # pragma: no cover — retry path
                last_err = e
                logger.warning(
                    "anthropic.messages.create attempt %d failed: %s",
                    attempt + 1,
                    e,
                )
                if attempt + 1 == self.max_retries:
                    raise ProviderUnavailableError(str(e)) from e
                await asyncio.sleep(2**attempt)

        latency_ms = int((time.perf_counter() - start) * 1000)
        assert raw_resp is not None, last_err

        usage = getattr(raw_resp, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) if usage else 0
        cache_create = getattr(usage, "cache_creation_input_tokens", 0) if usage else 0

        text_chunks: list[str] = []
        content_blocks: list[dict[str, Any]] = []
        for block in raw_resp.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_chunks.append(block.text)
                content_blocks.append({"type": "text", "text": block.text})
            elif block_type == "tool_use":
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
            else:
                content_blocks.append({"type": block_type, "raw": str(block)})

        cost = self._compute_cost(
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_create,
        )

        return ChatResponse(
            text="".join(text_chunks),
            content_blocks=content_blocks,
            model=model_id,
            provider=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_create,
            cost_usd=cost,
            latency_ms=latency_ms,
            stop_reason=getattr(raw_resp, "stop_reason", None),
            raw=raw_resp,
        )

    def _get_sdk(self):
        if self._sdk is None:
            from anthropic import AsyncAnthropic

            self._sdk = AsyncAnthropic(api_key=self.api_key)
        return self._sdk

    @staticmethod
    def _compute_cost(
        *,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int,
        cache_creation_tokens: int,
    ) -> Decimal:
        prices = _ANTHROPIC_PRICES.get(model_id)
        if prices is None:
            return Decimal("0")
        in_rate = prices["input"]
        out_rate = prices["output"]
        cost = (
            (input_tokens / 1_000_000) * in_rate
            + (output_tokens / 1_000_000) * out_rate
            + (cache_read_tokens / 1_000_000) * in_rate * _CACHE_READ_MULTIPLIER
            + (cache_creation_tokens / 1_000_000) * in_rate * _CACHE_WRITE_MULTIPLIER
        )
        return Decimal(str(round(cost, 6)))
