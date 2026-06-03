"""LLM client wrapper — provider-routed, cost-tracked, consent-gated.

This is the only sanctioned path for LLM calls in the codebase. Direct
use of the Anthropic or OpenAI SDK outside this module is a bug —
bypasses the cost ledger, the per-student cap, the consent gate, and
the spec-03 failover policy.

Spec 03 changes (May 2026)
--------------------------
- Three tiers: flagship (Opus 4.8) / workhorse (Sonnet 4.6) / batch
  (Haiku 4.5). Existing callers use `model="sonnet"|"haiku"` and keep
  working — those literals map to workhorse/batch internally.
- Provider abstraction: every call resolves the agent's preferred
  provider via `providers/registry.py`, with a failover list per §9.
- Consent gate: every call resolves the student's consent_mask via
  `ai/consent.py` BEFORE the request. Denial → ConsentDeniedError +
  ledger row with failure_reason='consent_denied'.
- Audit ledger expansion: every row carries provider, success,
  failure_reason, consent_mask, request_started_at, request_completed_at.

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
import datetime as _dt
import logging
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.consent import get_consent_mask, is_call_permitted
from unipaith.ai.providers import (
    ChatRequest,
    ProviderError,
    list_failover_order,
)
from unipaith.config import settings

logger = logging.getLogger(__name__)


# Spec 03 §11 — raised when a call is blocked by the student's consent
# mask. AIClient writes a `consent_denied` ledger row and re-raises so
# the calling service can route to its rule-based fallback.
class ConsentDeniedError(RuntimeError):
    def __init__(self, *, agent: str, denied_mask_key: str):
        self.agent = agent
        self.denied_mask_key = denied_mask_key
        super().__init__(f"Call denied by consent mask: agent={agent} needed={denied_mask_key}")


# Spec 03 §9 — raised after every configured provider has failed. The
# caller's rule-based fallback runs from here.
class AllProvidersFailedError(RuntimeError):
    def __init__(self, *, agent: str, attempts: int):
        self.agent = agent
        self.attempts = attempts
        super().__init__(
            f"All {attempts} providers failed for agent={agent}; "
            f"caller should run rule-based fallback"
        )


# ── Per-student cost cap (Plan 2 §10) ─────────────────────────────────────


class CostCapExceededError(RuntimeError):
    """Raised when a student has exhausted their weekly LLM budget and
    enforcement is set to `"block"`. Carries the spent amount and the cap
    so callers can surface a user-facing message ("You've hit your
    weekly limit — try again Monday")."""

    def __init__(self, *, student_id: uuid.UUID, spent_usd: float, cap_usd: float):
        self.student_id = student_id
        self.spent_usd = spent_usd
        self.cap_usd = cap_usd
        super().__init__(
            f"Cost cap exceeded for student={student_id}: ${spent_usd:.4f} > ${cap_usd:.4f}"
        )


async def student_cost_in_window(
    db: AsyncSession,
    student_id: uuid.UUID,
    *,
    window_days: int,
) -> float:
    """Return the sum of `ai_turns.cost_usd` for the student over the last
    `window_days`. Used by the per-student cap check.

    Returns 0.0 when no turns exist — the very first request for a
    student. Indexed read via `ix_ai_turns_student_created`.
    """
    # Local import — avoids the circular load when this module is imported
    # from `unipaith.models`.
    from unipaith.models.ai_artifacts import AiTurn

    since = _dt.datetime.now(_dt.UTC) - _dt.timedelta(days=window_days)
    total = await db.scalar(
        select(func.coalesce(func.sum(AiTurn.cost_usd), 0)).where(
            AiTurn.student_id == student_id,
            AiTurn.created_at >= since,
        )
    )
    return float(total or 0)


async def check_cost_cap(
    db: AsyncSession | None,
    student_id: uuid.UUID | None,
    *,
    cap_usd: float | None = None,
    window_days: int | None = None,
    enforcement: str | None = None,
) -> tuple[bool, float]:
    """Check whether a student is over the weekly LLM spend cap.

    Returns (over_cap, spent_usd). When `db` or `student_id` is None,
    returns (False, 0.0) — anonymous calls (eval harness, tests) skip
    enforcement.

    Caller is responsible for acting on the result. Used by both
    `AIClient.message()` and `AIClient.stream_message()` so the gate
    behaves the same across the two paths.
    """
    mode = enforcement if enforcement is not None else settings.ai_cost_cap_enforcement
    if mode == "off":
        return False, 0.0
    if db is None or student_id is None:
        return False, 0.0

    cap = cap_usd if cap_usd is not None else settings.ai_per_student_weekly_cost_cap_usd
    window = window_days if window_days is not None else settings.ai_cost_cap_window_days
    spent = await student_cost_in_window(db, student_id, window_days=window)
    return spent >= cap, spent


# ── Pricing table (USD per million tokens). Update when models/prices change.
# Cache reads bill at 0.1× input rate; cache writes (creation) at 1.25× input.
# Spec 03 §10 is the source of truth — keep in sync.
MODEL_PRICES: dict[str, dict[str, float]] = {
    # Anthropic (May 2026 prices, in $/MTok)
    "claude-opus-4-8": {"input": 15.00, "output": 75.00},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    # Backwards compat aliases — Anthropic's current GA models
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
    # OpenAI failover (spec 03 §9). Conservative GPT-4o family prices.
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    # Voyage embeddings ($/MTok input)
    "voyage-3-large": {"input": 0.18, "output": 0.0},
    "voyage-3": {"input": 0.06, "output": 0.0},
    # Spec 63 — self-hosted Qwen ML backend. Amortized GPU-hour estimate (the
    # real cost is tracked as GPU-hours in §14); far below the premium tiers.
    "qwen3-32b-instruct": {"input": 0.20, "output": 0.20},
    "qwen3-14b-instruct": {"input": 0.10, "output": 0.10},
    "qwen3-7b-instruct": {"input": 0.05, "output": 0.05},
    "qwen3-embedding-8b": {"input": 0.01, "output": 0.0},
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
    # Spec 06 §2 — institution review summary (Opus) + essay authenticity
    # (Haiku), and the L3 ML scorer's audit-ledger agent name.
    "review_summarizer",
    "authenticity_risk",
    "matcher",
    # Spec 10 §3 / 45 §12 — type-first program search query interpreter.
    "query_interpreter",
    # Spec 25 §10 / 45 §16 — institution campaign copy suggester.
    "campaign_copy",
    # Spec 20 §8 — Connect feed ranker + event recommender (Haiku).
    "connect_ranker",
    "event_recommender",
    # Spec 17 §7 / 45 §13 — inbox AI-suggested reply drafter.
    "inbox_reply_drafter",
    # Spec 24 §9 / 45 §19 — dataset upload parse triage (Haiku).
    "document_parse_triage",
]


# Legacy "sonnet"|"haiku" model labels (callers passed before the
# three-tier rollout) map to provider Protocol tier names.
_LEGACY_TIER_MAP: dict[str, str] = {
    "flagship": "flagship",
    "sonnet": "workhorse",
    "workhorse": "workhorse",
    "haiku": "batch",
    "batch": "batch",
}


def _tier_from_legacy(model: str) -> str:
    """Translate the legacy `model` literal to a provider Tier name.
    Keeps existing agent code (extractor, orchestrator, etc.) working
    without touching every call site."""
    return _LEGACY_TIER_MAP.get(model, "workhorse")


def _required_consent_key(agent: str) -> str:
    """Pretty-name the consent mask key blocking an agent. Used only
    for the ConsentDeniedError message + log line — the actual check
    is in `ai/consent.py`."""
    from unipaith.ai.consent import AGENT_REQUIRES

    return AGENT_REQUIRES.get(agent) or "unknown"


def _classify_failure(err: Exception) -> str:
    """Map a provider exception to a `failure_reason` enum value the
    audit ledger CHECK constraint accepts. Spec 03 §8."""
    from unipaith.ai.providers import ProviderTimeoutError

    if isinstance(err, ProviderTimeoutError):
        return "timeout"
    msg = str(err).lower()
    if "5" in msg and "0" in msg and ("server" in msg or "internal" in msg):
        return "provider_5xx"
    if "parse" in msg or "json" in msg:
        return "parse_error"
    return "unknown"


def _utcnow() -> _dt.datetime:
    """Wall-clock now in UTC. Wrapped so tests can swap it out."""
    return _dt.datetime.now(_dt.UTC)


@dataclass
class LLMResponse:
    """A complete LLM call result.

    `content_blocks` preserves Anthropic's tool-use blocks alongside text.
    `text` is the concatenation of text blocks for convenience.
    `cost_cap_warning` is set when the student is at/over the weekly
    spend cap and enforcement is set to `"warn"` — the call proceeded
    but the surface should show a soft-warn banner.
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
    cost_cap_warning: dict[str, Any] | None = None


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
        flagship_model: str | None = None,
    ):
        self.anthropic_api_key = anthropic_api_key
        self.voyage_api_key = voyage_api_key
        self.sonnet_model = sonnet_model
        self.haiku_model = haiku_model
        # Spec 03 §2 — Opus tier for "single defining moment" calls.
        self.flagship_model = (
            flagship_model if flagship_model is not None else settings.anthropic_default_flagship
        )
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
        model: Literal["sonnet", "haiku", "flagship"],
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
        """Send one provider-routed Messages request.

        Provider routing (spec 03 §5/§9):
          - resolves the agent's preferred provider via the registry
          - on timeout / 5xx, fails over to the next provider in
            `AI_PROVIDER_FAILOVER_CSV`
          - after all providers fail, raises AllProvidersFailedError so
            the caller's rule-based fallback runs (§7)
          - each attempt writes its own audit ledger row

        Consent gate (spec 03 §11):
          - resolves the student's consent_mask BEFORE the request
          - mask snapshot is written to the ledger row
          - denial raises ConsentDeniedError + writes a `rule_based`
            row with failure_reason='consent_denied'

        Caller is responsible for placing `cache_control` markers on
        cacheable blocks of `system` / `tools` / `messages` per the cache
        layout in spec 03 §3.

        Per-student weekly cost cap is enforced when both `db` and
        `student_id` are provided; mode is `settings.ai_cost_cap_enforcement`.

        Tier literal: `sonnet`|`haiku`|`flagship` map to
        workhorse|batch|flagship in provider Protocol terms. The two
        legacy names are kept so existing agent code (orchestrator,
        extractor, etc.) compiles unchanged.
        """
        tier = _tier_from_legacy(model)

        # Spec 03 §11 — consent gate.
        consent_mask = await get_consent_mask(db, student_id)
        if not is_call_permitted(agent, consent_mask):
            denied_key = _required_consent_key(agent)
            if db is not None:
                await self._log_consent_denied(
                    db=db,
                    agent=agent,
                    student_id=student_id,
                    discovery_message_id=discovery_message_id,
                    surface=surface,
                    consent_mask=consent_mask,
                )
            raise ConsentDeniedError(agent=agent, denied_mask_key=denied_key)

        cap_warning = await self._enforce_cost_cap(db, student_id, agent=agent)

        if self.mock_mode:
            resp = self._mock_message(agent=agent, tier=tier)
            resp.cost_cap_warning = cap_warning
            return resp

        providers = list_failover_order(agent)
        if not providers:
            raise AllProvidersFailedError(agent=agent, attempts=0)

        request = ChatRequest(
            tier=tier,
            system=system,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_ms=int(settings.ai_provider_failover_timeout_ms),
        )

        last_err: Exception | None = None
        for provider in providers:
            started_at = _utcnow()
            try:
                chat_resp = await provider.chat(request)
            except ProviderError as e:
                completed_at = _utcnow()
                last_err = e
                logger.warning("provider=%s agent=%s failed: %s", provider.name, agent, e)
                # Spec 03 §9 — every attempt gets a ledger row, including
                # failed ones, so cost dashboards can compute reliability.
                if db is not None:
                    await self._log_failed_turn(
                        db=db,
                        agent=agent,
                        student_id=student_id,
                        discovery_message_id=discovery_message_id,
                        surface=surface,
                        provider_name=provider.name,
                        model_id=provider.model_id(tier),
                        consent_mask=consent_mask,
                        failure_reason=_classify_failure(e),
                        started_at=started_at,
                        completed_at=completed_at,
                        error_msg=str(e),
                    )
                continue
            completed_at = _utcnow()

            response = LLMResponse(
                text=chat_resp.text,
                content_blocks=chat_resp.content_blocks,
                model=chat_resp.model,
                input_tokens=chat_resp.input_tokens,
                output_tokens=chat_resp.output_tokens,
                cache_read_tokens=chat_resp.cache_read_tokens,
                cache_creation_tokens=chat_resp.cache_creation_tokens,
                cost_usd=chat_resp.cost_usd,
                latency_ms=chat_resp.latency_ms,
                stop_reason=chat_resp.stop_reason,
                raw=chat_resp.raw,
                cost_cap_warning=cap_warning,
            )

            if db is not None:
                await self._log_turn(
                    db=db,
                    agent=agent,
                    student_id=student_id,
                    discovery_message_id=discovery_message_id,
                    surface=surface,
                    role="assistant",
                    provider_name=chat_resp.provider,
                    consent_mask=consent_mask,
                    started_at=started_at,
                    completed_at=completed_at,
                    response=response,
                )
            return response

        # All providers exhausted — caller runs rule-based fallback.
        raise AllProvidersFailedError(agent=agent, attempts=len(providers)) from last_err

    async def stream_message(
        self,
        *,
        agent: Agent,
        model: Literal["sonnet", "haiku", "flagship"],
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
        """Streaming variant of `message()` (Anthropic-only).

        Spec 03 §15 — streaming on the failover provider is deferred;
        the only streaming consumer today is the Discovery orchestrator
        and SSE there is Anthropic-native. On Anthropic failure we
        DON'T fail over to OpenAI for the stream (that would change the
        UX shape mid-message); we raise AllProvidersFailedError and the
        caller serves a rule-based message.

        Consent gate + cost cap + ledger fields match `message()` —
        provider on the row is always 'anthropic' for the streaming
        path.
        """
        tier = _tier_from_legacy(model)
        model_id = self._tier_to_anthropic_model_id(tier)

        # Spec 03 §11 — consent gate (same as message()).
        consent_mask = await get_consent_mask(db, student_id)
        if not is_call_permitted(agent, consent_mask):
            denied_key = _required_consent_key(agent)
            if db is not None:
                await self._log_consent_denied(
                    db=db,
                    agent=agent,
                    student_id=student_id,
                    discovery_message_id=discovery_message_id,
                    surface=surface,
                    consent_mask=consent_mask,
                )
            raise ConsentDeniedError(agent=agent, denied_mask_key=denied_key)

        cap_warning = await self._enforce_cost_cap(db, student_id, agent=agent)

        if self.mock_mode:
            mock_text = f"[mock-stream:{agent}:{model_id}]"
            yield ("text_delta", mock_text)
            response = LLMResponse(
                text=mock_text,
                content_blocks=[{"type": "text", "text": mock_text}],
                model=f"mock:{model_id}",
                stop_reason="end_turn",
                cost_cap_warning=cap_warning,
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
        started_at = _utcnow()
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
                usage["cache_read_input_tokens"] = getattr(u, "cache_read_input_tokens", 0) or 0
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
            cost_cap_warning=cap_warning,
        )
        if db is not None:
            await self._log_turn(
                db=db,
                agent=agent,
                student_id=student_id,
                discovery_message_id=discovery_message_id,
                surface=surface,
                role="assistant",
                provider_name="anthropic",
                consent_mask=consent_mask,
                started_at=started_at,
                completed_at=_utcnow(),
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
        """Generate a voyage-3-large embedding for the given text.

        Same cost-cap + consent gate as `message()`. Embedding is the
        cheapest path but matching-related, so consent.matching=false
        short-circuits to ConsentDeniedError (caller falls back to the
        rule-based feature pipeline).
        """
        consent_mask = await get_consent_mask(db, student_id)
        if not is_call_permitted("embedding", consent_mask):
            if db is not None:
                await self._log_consent_denied(
                    db=db,
                    agent="embedding",
                    student_id=student_id,
                    discovery_message_id=None,
                    surface=None,
                    consent_mask=consent_mask,
                )
            raise ConsentDeniedError(agent="embedding", denied_mask_key="matching")

        await self._enforce_cost_cap(db, student_id, agent="embedding")

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

        # Spec 63 §8 — embedding transport seam. Try Qwen3-Embedding when it is the
        # configured provider (Matryoshka-truncated to `embedding_dimension`), and
        # fall back to Voyage on any failure so flipping the provider is safe and a
        # Qwen outage never blocks featurization (§10/§16: never on a critical path).
        provider_name = "anthropic"  # Voyage rides under the Anthropic stack
        resp: EmbeddingResponse | None = None
        started_at = _utcnow()
        completed_at: _dt.datetime | None = None
        if settings.embedding_provider == "qwen" and settings.qwen_enabled:
            try:
                resp = await self._embed_qwen(text)
                provider_name = "qwen"
                completed_at = _utcnow()
            except Exception as e:  # pragma: no cover — network/SDK edge
                logger.warning("qwen embedding failed (%s); falling back to voyage", e)
                resp = None

        if resp is None:
            voyage = self._get_voyage()
            started_at = _utcnow()
            start = time.perf_counter()
            result = await asyncio.to_thread(
                voyage.embed,
                [text],
                model=self.embedding_model,
                input_type="document",
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            completed_at = _utcnow()
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
            provider_name = "anthropic"

        if db is not None:
            await self._log_embedding_turn(
                db=db,
                student_id=student_id,
                response=resp,
                consent_mask=consent_mask,
                started_at=started_at,
                completed_at=completed_at,
                provider=provider_name,
            )
        return resp

    async def _embed_qwen(self, text: str) -> EmbeddingResponse:
        """Spec 63 §8 — Qwen3-Embedding via the OpenAI-compatible ``/v1/embeddings``.

        Matryoshka-truncates the vector to ``settings.embedding_dimension`` so it
        slots into the live ``Vector`` store with no migration and no re-embed.
        Raises on any transport error — ``embed()`` catches it and falls back to
        Voyage, keeping a Qwen outage off the featurization critical path."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.qwen_api_key or "EMPTY",
            base_url=settings.qwen_base_url,
        )
        start = time.perf_counter()
        result = await client.embeddings.create(
            model=settings.qwen_embedding_model,
            input=[text],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        vec = list(result.data[0].embedding)
        dim = settings.embedding_dimension
        if len(vec) > dim:
            vec = vec[:dim]  # Matryoshka truncation → match the live column dim
        usage = getattr(result, "usage", None)
        tokens = 0
        if usage is not None:
            tokens = getattr(usage, "prompt_tokens", 0) or getattr(usage, "total_tokens", 0) or 0
        cost = self._compute_cost(
            model_id=settings.qwen_embedding_model,
            input_tokens=tokens,
            output_tokens=0,
            cache_read_tokens=0,
            cache_creation_tokens=0,
        )
        return EmbeddingResponse(
            embedding=vec,
            model=settings.qwen_embedding_model,
            input_tokens=tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )

    # ── Internals ────────────────────────────────────────────────────────

    @staticmethod
    async def _enforce_cost_cap(
        db: AsyncSession | None,
        student_id: uuid.UUID | None,
        *,
        agent: Agent,
    ) -> dict[str, Any] | None:
        """Cap-gate at the top of message() / stream_message().

        Returns a `cost_cap_warning` dict to attach to the response when
        enforcement is `"warn"` and the student is over the cap, None
        otherwise. Raises CostCapExceededError when enforcement is
        `"block"` and over.
        """
        if db is None or student_id is None:
            return None
        mode = settings.ai_cost_cap_enforcement
        if mode == "off":
            return None
        cap = settings.ai_per_student_weekly_cost_cap_usd
        window = settings.ai_cost_cap_window_days
        spent = await student_cost_in_window(db, student_id, window_days=window)
        if spent < cap:
            return None
        if mode == "block":
            raise CostCapExceededError(student_id=student_id, spent_usd=spent, cap_usd=cap)
        # mode == "warn" or anything else → soft warning.
        logger.warning(
            "AI cost cap warning: student=%s agent=%s spent=$%.4f cap=$%.4f window=%dd",
            student_id,
            agent,
            spent,
            cap,
            window,
        )
        return {
            "spent_usd": round(spent, 4),
            "cap_usd": round(cap, 4),
            "window_days": window,
            "mode": mode,
        }

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
        provider_name: str,
        consent_mask: dict[str, bool] | None,
        started_at: _dt.datetime,
        completed_at: _dt.datetime,
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
            model=response.model,
            provider=provider_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cache_read_tokens=response.cache_read_tokens,
            cache_creation_tokens=response.cache_creation_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
            success=True,
            failure_reason=None,
            consent_mask=consent_mask,
            request_started_at=started_at,
            request_completed_at=completed_at,
        )
        db.add(turn)
        await db.flush()

    @staticmethod
    async def _log_failed_turn(
        *,
        db: AsyncSession,
        agent: Agent,
        student_id: uuid.UUID | None,
        discovery_message_id: uuid.UUID | None,
        surface: str | None,
        provider_name: str,
        model_id: str,
        consent_mask: dict[str, bool] | None,
        failure_reason: str,
        started_at: _dt.datetime,
        completed_at: _dt.datetime,
        error_msg: str,
    ) -> None:
        """Spec 03 §9 — one ledger row per failed provider attempt.

        Lets the cost dashboard compute reliability per provider+agent.
        Zero tokens / zero cost because the provider didn't return a
        usable response.
        """
        from unipaith.models.ai_artifacts import AiTurn

        turn = AiTurn(
            student_id=student_id,
            discovery_message_id=discovery_message_id,
            agent=agent,
            surface=surface,
            role="assistant",
            model=model_id,
            provider=provider_name,
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            latency_ms=int((completed_at - started_at).total_seconds() * 1000),
            error=error_msg[:1000],
            success=False,
            failure_reason=failure_reason,
            consent_mask=consent_mask,
            request_started_at=started_at,
            request_completed_at=completed_at,
        )
        db.add(turn)
        await db.flush()

    @staticmethod
    async def _log_consent_denied(
        *,
        db: AsyncSession,
        agent: Agent,
        student_id: uuid.UUID | None,
        discovery_message_id: uuid.UUID | None,
        surface: str | None,
        consent_mask: dict[str, bool],
    ) -> None:
        """Spec 03 §11 — record a denied call. provider='rule_based'
        because the caller will run the deterministic path; the row
        documents the denial for the compliance audit."""
        from unipaith.models.ai_artifacts import AiTurn

        now = _utcnow()
        turn = AiTurn(
            student_id=student_id,
            discovery_message_id=discovery_message_id,
            agent=agent,
            surface=surface,
            role="assistant",
            model="rule_based",
            provider="rule_based",
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal("0"),
            latency_ms=0,
            success=False,
            failure_reason="consent_denied",
            consent_mask=consent_mask,
            request_started_at=now,
            request_completed_at=now,
        )
        db.add(turn)
        await db.flush()

    @staticmethod
    async def _log_embedding_turn(
        *,
        db: AsyncSession,
        student_id: uuid.UUID | None,
        response: EmbeddingResponse,
        consent_mask: dict[str, bool] | None = None,
        started_at: _dt.datetime | None = None,
        completed_at: _dt.datetime | None = None,
        provider: str = "anthropic",
    ) -> None:
        from unipaith.models.ai_artifacts import AiTurn

        turn = AiTurn(
            student_id=student_id,
            agent="embedding",
            role="tool",
            model=response.model,
            # Spec 63 — "qwen" when the Qwen embedder served it; else "anthropic"
            # (Voyage rides under the Anthropic stack). Lets the cost dashboard
            # split embedding spend by transport.
            provider=provider,
            input_tokens=response.input_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
            success=True,
            failure_reason=None,
            consent_mask=consent_mask,
            request_started_at=started_at,
            request_completed_at=completed_at,
        )
        db.add(turn)
        await db.flush()

    def _tier_to_anthropic_model_id(self, tier) -> str:
        if tier == "flagship":
            return self.flagship_model
        if tier == "batch":
            return self.haiku_model
        return self.sonnet_model

    def _mock_message(self, *, agent: Agent, tier) -> LLMResponse:
        model_id = self._tier_to_anthropic_model_id(tier)
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
