"""Spec 03 §5/§6/§9 — provider registry.

Resolves names to provider singletons, reads per-agent overrides from
`settings.ai_provider_per_agent_json`, and exposes the failover order
for the AIClient.

Behavior
--------
- `get_provider("anthropic")` — singleton lookup. Lazy-built.
- `get_provider_for_agent("match_rationale")` — returns the default
  provider unless the agent has an override.
- `list_failover_order(agent)` — returns the ordered list of available
  providers the AIClient should try. Unavailable providers (missing key,
  missing SDK) are skipped so failover doesn't burn a hop on a known
  no-op.

Thread-safety: singletons are created at first access; no locking
required because the registry is read-mostly and Python's GIL serializes
the dict access.
"""

from __future__ import annotations

import json
import logging

from unipaith.ai.boundary import enforce_policy
from unipaith.ai.providers.anthropic_provider import AnthropicProvider
from unipaith.ai.providers.base import AIProvider
from unipaith.ai.providers.openai_provider import OpenAIProvider
from unipaith.ai.providers.opensource_provider import OpenSourceProvider
from unipaith.ai.providers.qwen_provider import QwenProvider
from unipaith.config import settings

logger = logging.getLogger(__name__)


_providers: dict[str, AIProvider] = {}
_per_agent_cache: dict[str, str] | None = None


def _build_provider(name: str) -> AIProvider:
    """Construct a concrete provider by name. Add new providers here."""
    if name == "anthropic":
        return AnthropicProvider()
    if name == "openai":
        return OpenAIProvider()
    if name == "opensource":
        # The Qwen-via-Together transport — the migration target (single LLM
        # provider once OPENSOURCE_API_KEY is wired). Lazily built; inert with no
        # key (is_available returns False → caller runs the rule-based fallback).
        return OpenSourceProvider()
    if name == "qwen":
        # Spec 63 — the Qwen ML backend transport. Registered + lazily built;
        # inert until `qwen_enabled` (see QwenProvider.is_available).
        return QwenProvider()
    if name == "rule_based":
        # Sentinel — never actually instantiated. The AIClient short-
        # circuits to the per-agent rule-based path before reaching the
        # provider call. Raising here makes the misuse obvious.
        raise ValueError(
            "rule_based is not a real provider — caller must invoke the "
            "agent's rule-based fallback directly"
        )
    raise ValueError(f"Unknown AI provider: {name!r}")


def get_provider(name: str) -> AIProvider:
    """Return the singleton provider by name. Lazy-built on first call."""
    if name not in _providers:
        _providers[name] = _build_provider(name)
    return _providers[name]


def _load_per_agent_overrides() -> dict[str, str]:
    """Parse `settings.ai_provider_per_agent_json` once and cache."""
    global _per_agent_cache
    if _per_agent_cache is not None:
        return _per_agent_cache
    raw = (settings.ai_provider_per_agent_json or "").strip()
    if not raw:
        _per_agent_cache = {}
        return _per_agent_cache
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("AI_PROVIDER_PER_AGENT_JSON must be a JSON object")
        _per_agent_cache = {str(k): str(v) for k, v in parsed.items()}
    except (ValueError, json.JSONDecodeError) as e:  # pragma: no cover — env edge
        logger.warning(
            "AI_PROVIDER_PER_AGENT_JSON is invalid (%s); using default for all agents",
            e,
        )
        _per_agent_cache = {}
    return _per_agent_cache


def get_provider_for_agent(agent: str) -> AIProvider:
    """Return the configured provider for an agent. Falls back to
    `ai_provider_default` when no override is set.

    Spec 63 — the hard boundary is applied here on every resolution:
    ``enforce_policy`` forces a human-facing agent back to Claude even if
    ``ai_provider_per_agent_json`` (or the default) tries to route it to the Qwen
    ML backend. The pin cannot be configured away."""
    overrides = _load_per_agent_overrides()
    name = overrides.get(agent, settings.ai_provider_default)
    name = enforce_policy(agent, name)
    return get_provider(name)


def list_failover_order(agent: str) -> list[AIProvider]:
    """Return providers to try in order. Skips unavailable providers so
    the AIClient doesn't waste a failover hop on a missing key.

    Per spec 03 §9, the order is configured globally
    (`ai_provider_failover_csv`) but the FIRST attempt always uses the
    agent's preferred provider — overrides take precedence over the
    failover list's lead element.
    """
    preferred = get_provider_for_agent(agent)  # already policy-pinned
    failover_names = [n.strip() for n in settings.ai_provider_failover_csv.split(",") if n.strip()]
    ordered: list[AIProvider] = [preferred]
    seen: set[str] = {preferred.name}
    for name in failover_names:
        if name == "rule_based":
            continue  # not a real provider
        # Spec 63 — the boundary also filters the failover chain: a human-facing
        # agent is never failed over to the Qwen ML backend. (Maps qwen → Claude,
        # which then dedups against the already-present preferred.)
        name = enforce_policy(agent, name)
        if name in seen:
            continue  # already in the chain (incl. the policy-pinned preferred)
        try:
            p = get_provider(name)
        except ValueError:
            continue  # unknown provider; skip
        ordered.append(p)
        seen.add(name)
    # Filter unavailable providers so we don't log a failure attempt on
    # a known no-op. Keep the preferred regardless so the caller sees
    # the same error shape as before (config bug vs. runtime).
    available = [ordered[0]] + [p for p in ordered[1:] if p.is_available()]
    return available


def reset_registry() -> None:
    """Test helper: clears all cached singletons + overrides."""
    global _per_agent_cache
    _providers.clear()
    _per_agent_cache = None
