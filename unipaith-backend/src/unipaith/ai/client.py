"""Anthropic + Voyage client wrapper with cost tracking, retries, and caching.

This is the only sanctioned path for LLM calls in the codebase. Direct use of
the Anthropic SDK outside this module is a bug — bypasses the cost ledger and
the per-student cap.

Design
------
- One singleton (`get_client()`) per process. Holds the Anthropic and Voyage
  SDK instances. Cheap to instantiate; we use a singleton so the SDKs reuse
  HTTP connection pools.
- Every call writes one row to `ai_turns` via `_log_turn()`. Caller passes
  `agent` (one of the 8 allowed values from the CHECK constraint) and an
  optional `student_id` + `discovery_message_id` for joinability.
- `mock_mode` (driven by `settings.ai_mock_mode`) returns canned responses so
  unit tests don't burn tokens. Eval harness uses real mode unless the
  fixture itself is marked deterministic.
- Cost calculation uses Anthropic's published per-MTok prices. Update
  `MODEL_PRICES` when models or prices change. Cache reads are billed at 0.1×
  the input rate.

What's deliberately NOT here
----------------------------
- No agent-specific logic. Each agent (orchestrator, extractor, etc.) lives
  in its own module (A2+) and calls into this client.
- No prompt caching breakpoints — those are passed in by the caller. The
  client just forwards `cache_control` on the relevant blocks.
- No streaming yet — `message()` is buffered. Streaming comes in A2 along
  with the orchestrator (which is the only streaming consumer in scope).
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings

logger = logging.getLogger(__name__)


# ── Pricing table (USD per million tokens). Update when models/prices change.
# Cache reads bill at 0.1× input rate; cache writes (creation) at 1.25× input.
MODEL_PRICES: dict[str, dict[str, float]] = {
    # Anthropic (May 2026 prices, in $/MTok)
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},
    # Backwards compat aliases — Anthropic's current GA models
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
    # Voyage embeddings ($/MTok input)
    "voyage-3-large": {"input": 0.18, "output": 0.0},
    "voyage-3": {"input": 0.06, "output": 0.0},
}

CACHE_READ_MULTIPLIER = 0.1
CACHE_WRITE_MULTIPLIER = 1.25


# Allowed `agent` values — must match CHECK constraint on ai_turns.
Agent = Literal[
    "orchestrator",
    "extractor",
    "validator",
    "feature_emitter",
    "rationale",
    "workshop_coach",
    "workshop_judge",
    "embedding",
]


@dataclass
class LLMResponse:
    """A complete LLM call result.

    `content_blocks` preserves Anthropic's tool-use blocks alongside text.
    `text` is the concatenation of text blocks for convenience.
    """

    text: str
    content_blocks: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: Decimal = Decimal("0")
    latency_ms: int = 0
    stop_reason: str | None = None
    raw: Any | None = None


@dataclass
class EmbeddingResponse:
    embedding: list[float]
    model: str
    input_tokens: int = 0
    cost_usd: Decimal = Decimal("0")
    latency_ms: int = 0


class AIClient:
    """Wrapper around the Anthropic SDK and Voyage embedding API.

    Use the module-level `get_client()` to obtain the singleton.
    """

    def __init__(
        self,
        anthropic_api_key: str,
        voyage_api_key: str,
        sonnet_model: str,
        haiku_model: str,
        embedding_model: str,
        mock_mode: bool = False,
        max_retries: int = 3,
        request_timeout: int = 45,
    ):
        self.anthropic_api_key = anthropic_api_key
        self.voyage_api_key = voyage_api_key
        self.sonnet_model = sonnet_model
        self.haiku_model = haiku_model
        self.embedding_model = embedding_model
        self.mock_mode = mock_mode
        self.max_retries = max_retries
        self.request_timeout = request_timeout

        # Lazy SDK init — keeps test imports cheap and lets us run in mock mode
        # on dev boxes that don't have the packages installed yet.
        self._anthropic = None
        self._voyage = None

    # ── Public API ───────────────────────────────────────────────────────

    async def message(
        self,
        *,
        agent: Agent,
        model: Literal["sonnet", "haiku"],
        system: list[dict[str, Any]] | str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        student_id: uuid.UUID | None = None,
        discovery_message_id: uuid.UUID | None = None,
        surface: str | None = None,
        db: AsyncSession | None = None,
    ) -> LLMResponse:
        """Send a single Anthropic Messages API request.

        Caller is responsible for placing `cache_control` markers on
        cacheable blocks of `system` / `tools` / `messages` per the cache
        layout in §5 of the plan.

        If `db` is provided, a row is written to `ai_turns` after the call.
        Callers without an active session (e.g. eval harness) can pass None.
        """
        model_id = self.sonnet_model if model == "sonnet" else self.haiku_model

        if self.mock_mode:
            return self._mock_message(agent=agent, model_id=model_id)

        anthropic = self._get_anthropic()

        params: dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": messages,
        }
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice

        # Prompt caching is opt-in via cache_control markers placed by the
        # caller. The header below tells Anthropic the request may carry them.
        extra_headers = {"anthropic-beta": "prompt-caching-2024-07-31"}

        start = time.perf_counter()
        last_err: Exception | None = None
        raw_resp = None
        for attempt in range(self.max_retries):
            try:
                raw_resp = await anthropic.messages.create(
                    **params,
                    extra_headers=extra_headers,
                    timeout=self.request_timeout,
                )
                break
            except Exception as e:  # pragma: no cover — retry path
                last_err = e
                logger.warning(
                    "anthropic.messages.create attempt %d failed: %s",
                    attempt + 1,
                    e,
                )
                if attempt + 1 == self.max_retries:
                    raise
                await asyncio.sleep(2**attempt)
        latency_ms = int((time.perf_counter() - start) * 1000)

        assert raw_resp is not None, last_err  # for mypy

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

        response = LLMResponse(
            text="".join(text_chunks),
            content_blocks=content_blocks,
            model=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_create,
            cost_usd=cost,
            latency_ms=latency_ms,
            stop_reason=getattr(raw_resp, "stop_reason", None),
            raw=raw_resp,
        )

        if db is not None:
            await self._log_turn(
                db=db,
                agent=agent,
                student_id=student_id,
                discovery_message_id=discovery_message_id,
                surface=surface,
                role="assistant",
                model=model_id,
                response=response,
            )

        return response

    async def stream_message(
        self,
        *,
        agent: Agent,
        model: Literal["sonnet", "haiku"],
        system: list[dict[str, Any]] | str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        student_id: uuid.UUID | None = None,
        discovery_message_id: uuid.UUID | None = None,
        surface: str | None = None,
        db: AsyncSession | None = None,
    ):
        """Streaming variant of `message()`.

        Yields tuples (event_type, payload) where:
          - ('text_delta', str)        — incremental text chunk
          - ('tool_use', dict)         — completed tool_use block (parsed input)
          - ('done', LLMResponse)      — final aggregated response with cost

        After the generator exhausts, one row is written to `ai_turns` with
        full token + cost accounting (when db is provided). Mock mode emits
        a single text_delta then 'done'.
        """
        model_id = self.sonnet_model if model == "sonnet" else self.haiku_model

        if self.mock_mode:
            mock_text = f"[mock-stream:{agent}:{model_id}]"
            yield ("text_delta", mock_text)
            response = LLMResponse(
                text=mock_text,
                content_blocks=[{"type": "text", "text": mock_text}],
                model=f"mock:{model_id}",
                stop_reason="end_turn",
            )
            yield ("done", response)
            return

        anthropic = self._get_anthropic()
        params: dict[str, Any] = {
            "model": model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": messages,
        }
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        extra_headers = {"anthropic-beta": "prompt-caching-2024-07-31"}

        start = time.perf_counter()
        text_chunks: list[str] = []
        content_blocks: list[dict[str, Any]] = []
        usage: dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        }
        stop_reason: str | None = None

        async with anthropic.messages.stream(
            **params, extra_headers=extra_headers, timeout=self.request_timeout
        ) as stream:
            async for event in stream:
                etype = getattr(event, "type", None)
                if etype == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    if delta is not None and getattr(delta, "type", None) == "text_delta":
                        chunk = delta.text
                        text_chunks.append(chunk)
                        yield ("text_delta", chunk)
                elif etype == "content_block_stop":
                    block = getattr(event, "content_block", None)
                    if block is not None and getattr(block, "type", None) == "tool_use":
                        tu = {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                        content_blocks.append(tu)
                        yield ("tool_use", tu)

            final_msg = await stream.get_final_message()
            stop_reason = getattr(final_msg, "stop_reason", None)
            u = getattr(final_msg, "usage", None)
            if u is not None:
                usage["input_tokens"] = getattr(u, "input_tokens", 0) or 0
                usage["output_tokens"] = getattr(u, "output_tokens", 0) or 0
                usage["cache_read_input_tokens"] = (
                    getattr(u, "cache_read_input_tokens", 0) or 0
                )
                usage["cache_creation_input_tokens"] = (
                    getattr(u, "cache_creation_input_tokens", 0) or 0
                )

        latency_ms = int((time.perf_counter() - start) * 1000)
        full_text = "".join(text_chunks)
        if full_text and not any(b.get("type") == "text" for b in content_blocks):
            content_blocks.insert(0, {"type": "text", "text": full_text})

        cost = self._compute_cost(
            model_id=model_id,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            cache_read_tokens=usage["cache_read_input_tokens"],
            cache_creation_tokens=usage["cache_creation_input_tokens"],
        )
        response = LLMResponse(
            text=full_text,
            content_blocks=content_blocks,
            model=model_id,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            cache_read_tokens=usage["cache_read_input_tokens"],
            cache_creation_tokens=usage["cache_creation_input_tokens"],
            cost_usd=cost,
            latency_ms=latency_ms,
            stop_reason=stop_reason,
        )
        if db is not None:
            await self._log_turn(
                db=db,
                agent=agent,
                student_id=student_id,
                discovery_message_id=discovery_message_id,
                surface=surface,
                role="assistant",
                model=model_id,
                response=response,
            )
        yield ("done", response)

    async def embed(
        self,
        text: str,
        *,
        student_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
    ) -> EmbeddingResponse:
        """Generate a voyage-3-large embedding for the given text."""
        if self.mock_mode:
            # Deterministic mock: hash-derived 1024-d vector in [-1, 1].
            import hashlib
            import struct

            digest = hashlib.sha256(text.encode("utf-8")).digest()
            # Repeat digest until we have 4096 bytes for 1024 floats.
            buf = (digest * ((4096 // len(digest)) + 1))[:4096]
            vec = list(struct.unpack("1024f", buf))
            # Normalize to [-1, 1].
            vec = [max(-1.0, min(1.0, v / 1e30)) for v in vec]
            return EmbeddingResponse(embedding=vec, model=f"mock:{self.embedding_model}")

        voyage = self._get_voyage()
        start = time.perf_counter()
        result = await asyncio.to_thread(
            voyage.embed,
            [text],
            model=self.embedding_model,
            input_type="document",
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        embedding = result.embeddings[0]
        # Voyage SDK returns total_tokens on the response object.
        tokens = getattr(result, "total_tokens", 0)

        cost = self._compute_cost(
            model_id=self.embedding_model,
            input_tokens=tokens,
            output_tokens=0,
            cache_read_tokens=0,
            cache_creation_tokens=0,
        )
        resp = EmbeddingResponse(
            embedding=embedding,
            model=self.embedding_model,
            input_tokens=tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )
        if db is not None:
            await self._log_embedding_turn(db=db, student_id=student_id, response=resp)
        return resp

    # ── Internals ────────────────────────────────────────────────────────

    def _get_anthropic(self):
        if self._anthropic is None:
            from anthropic import AsyncAnthropic

            self._anthropic = AsyncAnthropic(api_key=self.anthropic_api_key)
        return self._anthropic

    def _get_voyage(self):
        if self._voyage is None:
            import voyageai

            self._voyage = voyageai.Client(api_key=self.voyage_api_key)
        return self._voyage

    @staticmethod
    def _compute_cost(
        *,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int,
        cache_creation_tokens: int,
    ) -> Decimal:
        prices = MODEL_PRICES.get(model_id)
        if prices is None:
            return Decimal("0")
        in_rate = prices["input"]
        out_rate = prices["output"]
        cost = (
            (input_tokens / 1_000_000) * in_rate
            + (output_tokens / 1_000_000) * out_rate
            + (cache_read_tokens / 1_000_000) * in_rate * CACHE_READ_MULTIPLIER
            + (cache_creation_tokens / 1_000_000) * in_rate * CACHE_WRITE_MULTIPLIER
        )
        return Decimal(str(round(cost, 6)))

    @staticmethod
    async def _log_turn(
        *,
        db: AsyncSession,
        agent: Agent,
        student_id: uuid.UUID | None,
        discovery_message_id: uuid.UUID | None,
        surface: str | None,
        role: str,
        model: str,
        response: LLMResponse,
    ) -> None:
        # Local import — avoids circular import on package load.
        from unipaith.models.ai_artifacts import AiTurn

        turn = AiTurn(
            student_id=student_id,
            discovery_message_id=discovery_message_id,
            agent=agent,
            surface=surface,
            role=role,
            model=model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cache_read_tokens=response.cache_read_tokens,
            cache_creation_tokens=response.cache_creation_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
        )
        db.add(turn)
        await db.flush()

    @staticmethod
    async def _log_embedding_turn(
        *,
        db: AsyncSession,
        student_id: uuid.UUID | None,
        response: EmbeddingResponse,
    ) -> None:
        from unipaith.models.ai_artifacts import AiTurn

        turn = AiTurn(
            student_id=student_id,
            agent="embedding",
            role="tool",
            model=response.model,
            input_tokens=response.input_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
        )
        db.add(turn)
        await db.flush()

    @staticmethod
    def _mock_message(*, agent: Agent, model_id: str) -> LLMResponse:
        return LLMResponse(
            text=f"[mock:{agent}:{model_id}]",
            content_blocks=[{"type": "text", "text": f"[mock:{agent}:{model_id}]"}],
            model=f"mock:{model_id}",
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            latency_ms=0,
            stop_reason="end_turn",
        )


# ── Singleton ───────────────────────────────────────────────────────────────

_client: AIClient | None = None


def get_client() -> AIClient:
    """Return the process-wide AIClient singleton.

    Reads config from `unipaith.config.settings`. In tests, set
    `ai_mock_mode=true` to short-circuit live API calls.
    """
    global _client
    if _client is not None:
        return _client

    _client = AIClient(
        anthropic_api_key=settings.anthropic_api_key,
        voyage_api_key=settings.voyage_api_key,
        sonnet_model=settings.llm_reasoning_model,
        haiku_model=settings.llm_feature_model,
        embedding_model=settings.embedding_model,
        mock_mode=settings.ai_mock_mode,
        max_retries=settings.ai_request_max_retries,
        request_timeout=settings.ai_request_timeout_seconds,
    )
    return _client


def reset_client() -> None:
    """Test helper — clears the singleton so a fresh one is built next call."""
    global _client
    _client = None
