"""Spec 03 §5 — provider Protocol + shared types.

A provider is anything that can turn a (system, messages, tools) triple
into a ChatResponse. The two concrete providers in this codebase are
Anthropic (Claude) and OpenAI (GPT-4o family, retained as failover per
§9). Bedrock is reserved for the future (spec 03 §15).

The shape is deliberately minimal:
- Inputs match Anthropic's Messages API (the spec's primary). The
  OpenAI provider translates internally — it's the second-class
  citizen, not the abstraction's center of gravity.
- The provider does NOT write the ledger. The AIClient owns logging so
  the per-attempt audit row in §9 is emitted in a consistent place
  across failover hops.
- Errors raise typed exceptions so AIClient can decide retry vs
  failover vs rule-based fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal, Protocol, runtime_checkable

# Tier names map to a model ID per provider. The provider looks up the
# concrete model from its own settings; the agent only names a tier.
Tier = Literal["flagship", "workhorse", "batch"]


class ProviderError(RuntimeError):
    """Base for provider-side failures. AIClient catches these to decide
    whether to retry, fail over, or fall back to rule-based."""


class ProviderTimeoutError(ProviderError):
    """The provider exceeded the configured per-request timeout."""


class ProviderUnavailableError(ProviderError):
    """The provider returned 5xx, the SDK is missing, or the API key is
    empty. Treated identically to a timeout by the failover policy."""


@dataclass
class ChatRequest:
    """Input to `AIProvider.chat()`. Shape matches Anthropic Messages
    closely — providers translate as needed.

    - `tier` lets the agent stay provider-agnostic; the provider maps
      tier → its own model ID.
    - `system` and `messages` follow Anthropic's content-block schema
      (list-of-blocks for cache_control). OpenAI provider flattens.
    - `cache_control_layout` is informational metadata so providers can
      emit the right beta headers without re-parsing message bodies.
    """

    tier: Tier
    system: list[dict[str, Any]] | str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] | None = None
    tool_choice: dict[str, Any] | None = None
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout_ms: int = 30_000
    cache_control_layout: str = "system_1h+persona_5min+tail"


@dataclass
class ChatResponse:
    """Output of `AIProvider.chat()`.

    The fields mirror what `AIClient.LLMResponse` cares about — token
    usage + cost-precursor numbers + the actual text / tool_use blocks.
    AIClient stamps the audit row from this plus its own start/end
    timestamps.
    """

    text: str
    content_blocks: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: Decimal = Decimal("0")
    latency_ms: int = 0
    stop_reason: str | None = None
    raw: Any | None = None


@runtime_checkable
class AIProvider(Protocol):
    """The contract every provider satisfies. Used by registry +
    AIClient. New providers (Bedrock, on-prem llama, etc.) implement
    this and register in `providers/registry.py`."""

    name: str

    async def chat(self, request: ChatRequest) -> ChatResponse:  # pragma: no cover
        """Issue one chat request. Raise ProviderTimeoutError /
        ProviderUnavailableError on infra failure; raise ValueError on
        bad input. Successful return → audit row written by caller."""
        ...

    def is_available(self) -> bool:  # pragma: no cover
        """Cheap check the caller uses before adding this provider to a
        failover round (e.g., empty API key → not available)."""
        ...

    def model_id(self, tier: Tier) -> str:  # pragma: no cover
        """Resolve a tier name to the provider's concrete model ID.
        Stamped onto the audit row so cost dashboards can split by
        model."""
        ...
