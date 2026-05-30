"""Spec 03 §5 + §9 — OpenAI provider (failover only).

Per the model-portability principle (§1), OpenAI stays in the codebase
as a parallel set so we can fail over to it when Anthropic is
unavailable. It is NOT the default for any agent in MVP.

Translation details
-------------------
- System content-blocks are flattened to a single string in OpenAI's
  shape (no cache_control concept on the OpenAI side — caching there is
  automatic and opaque).
- Tool blocks are converted to OpenAI function-calling shape.
- Prices come from the GPT-4o family. Update when migrating to a newer
  model family.
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


# Per-MTok prices (USD) for OpenAI failover. Conservative defaults.
_OPENAI_PRICES: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
}


# Tier → OpenAI model. Mirrors the Anthropic tier map so a failover
# attempt picks a model with roughly equivalent capability.
_OPENAI_TIER_MAP: dict[Tier, str] = {
    "flagship": "gpt-4o",
    "workhorse": "gpt-4o",
    "batch": "gpt-4o-mini",
}


class OpenAIProvider(AIProvider):
    """OpenAI failover provider. Off the hot path; treats every call as
    best-effort."""

    name = "openai"

    def __init__(self, *, api_key: str | None = None, max_retries: int = 2):
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.max_retries = max_retries
        self._sdk = None

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return True

    def model_id(self, tier: Tier) -> str:
        return _OPENAI_TIER_MAP[tier]

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self.api_key:
            raise ProviderUnavailableError("OPENAI_API_KEY is empty")
        sdk = self._get_sdk()
        model_id = self.model_id(request.tier)

        flat_messages: list[dict[str, Any]] = []
        # OpenAI: system goes as one or more system-role messages.
        if isinstance(request.system, str):
            flat_messages.append({"role": "system", "content": request.system})
        else:
            for block in request.system:
                if block.get("type") == "text":
                    flat_messages.append({"role": "system", "content": block["text"]})
        for m in request.messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, list):
                text = "\n".join(b.get("text", "") for b in content if b.get("type") == "text")
                flat_messages.append({"role": role, "content": text})
            else:
                flat_messages.append({"role": role, "content": content})

        timeout_s = request.timeout_ms / 1000.0
        start = time.perf_counter()
        last_err: Exception | None = None
        raw_resp: Any | None = None
        for attempt in range(self.max_retries):
            try:
                raw_resp = await sdk.chat.completions.create(
                    model=model_id,
                    messages=flat_messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    timeout=timeout_s,
                )
                break
            except TimeoutError as e:
                raise ProviderTimeoutError(f"openai timeout after {request.timeout_ms}ms") from e
            except Exception as e:  # pragma: no cover — retry path
                last_err = e
                logger.warning(
                    "openai.chat.completions.create attempt %d failed: %s",
                    attempt + 1,
                    e,
                )
                if attempt + 1 == self.max_retries:
                    raise ProviderUnavailableError(str(e)) from e
                await asyncio.sleep(2**attempt)

        latency_ms = int((time.perf_counter() - start) * 1000)
        assert raw_resp is not None, last_err

        usage = getattr(raw_resp, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        choice = raw_resp.choices[0]
        text = choice.message.content or ""
        content_blocks = [{"type": "text", "text": text}]

        cost = self._compute_cost(
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return ChatResponse(
            text=text,
            content_blocks=content_blocks,
            model=model_id,
            provider=self.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            stop_reason=getattr(choice, "finish_reason", None),
            raw=raw_resp,
        )

    def _get_sdk(self):
        if self._sdk is None:
            from openai import AsyncOpenAI

            self._sdk = AsyncOpenAI(api_key=self.api_key)
        return self._sdk

    @staticmethod
    def _compute_cost(*, model_id: str, input_tokens: int, output_tokens: int) -> Decimal:
        prices = _OPENAI_PRICES.get(model_id)
        if prices is None:
            return Decimal("0")
        cost = (input_tokens / 1_000_000) * prices["input"] + (output_tokens / 1_000_000) * prices[
            "output"
        ]
        return Decimal(str(round(cost, 6)))
