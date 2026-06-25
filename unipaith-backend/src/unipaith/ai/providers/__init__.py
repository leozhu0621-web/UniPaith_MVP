"""Spec 03 §5 — provider abstraction.

Routing surface for the LLM stack. Every agent calls
`get_provider(name).chat(...)`. The agent never sees Anthropic vs OpenAI
vs Bedrock vs the rule-based path — those choices live here.

Why this layer exists
---------------------
- Provider-level failover (anthropic → openai → rule-based) without
  bloating each agent module with retry trees.
- Per-agent provider overrides via env (`AI_PROVIDER_PER_AGENT_JSON`)
  so a noisy or expensive call site can be rerouted without a deploy.
- A single chokepoint for prompt-cache headers + token accounting.
- Compliance audit can verify provider routing matches the configured
  default by reading `ai_turns.provider`.

The Anthropic and OpenAI providers wrap their respective SDKs.
Bedrock is a stub for now — spec 03 §15 says "defer until requested".
The rule-based provider is NOT here; it lives next to each agent
because the deterministic fallback shape is agent-specific.
"""

from unipaith.ai.providers.anthropic_provider import AnthropicProvider
from unipaith.ai.providers.base import (
    AIProvider,
    ChatRequest,
    ChatResponse,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from unipaith.ai.providers.openai_provider import OpenAIProvider
from unipaith.ai.providers.opensource_provider import OpenSourceProvider
from unipaith.ai.providers.qwen_provider import QwenProvider
from unipaith.ai.providers.registry import (
    get_provider,
    get_provider_for_agent,
    list_failover_order,
    reset_registry,
)

__all__ = [
    "AIProvider",
    "ChatRequest",
    "ChatResponse",
    "ProviderError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "AnthropicProvider",
    "OpenAIProvider",
    "OpenSourceProvider",
    "QwenProvider",
    "get_provider",
    "get_provider_for_agent",
    "list_failover_order",
    "reset_registry",
]
