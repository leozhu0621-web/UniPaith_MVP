"""UniPaith AI package.

Phase progression
-----------------
- A1 (shipped): Anthropic client wrapper, prompt files, extractor schema,
  eval harness, DB foundations.
- A2 (this phase): Discovery BASIC layer end-to-end —
  Orchestrator + Extractor + (deterministic BASIC) Validator +
  artifact-writer wired into the discovery service behind a flag.
- A3 (next): personality + identity layers, LLM-as-judge validator,
  bias-pair fixtures, SSE streaming.
- B+: feature emitter, ML matcher, rationale agent, workshop coaches.

All LLM calls in the application MUST go through `unipaith.ai.client.AIClient`.
This is enforced by:
  - the cost ledger (`ai_turns` table) — every call writes a row
  - the per-student cost cap — checked before each call
  - the prompt-cache layout — built into the client, not duplicated per agent

External code imports either the client singleton (low-level) or one of the
agent singletons (high-level):

    from unipaith.ai import get_client, get_orchestrator, get_extractor
"""

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.extractor import (
    ExtractedSignals,
    Extractor,
    get_extractor,
    reset_extractor,
)
from unipaith.ai.orchestrator import (
    Orchestrator,
    OrchestratorResponse,
    TurnContext,
    get_orchestrator,
    reset_orchestrator,
)
from unipaith.ai.state import LayerVerdict, StudentSnapshot, evaluate_basic_layer
from unipaith.ai.validator import LayerValidator, default_validator

__all__ = [
    # client
    "AIClient",
    "get_client",
    # orchestrator (A1 agent)
    "Orchestrator",
    "OrchestratorResponse",
    "TurnContext",
    "get_orchestrator",
    "reset_orchestrator",
    # extractor (A2 agent)
    "ExtractedSignals",
    "Extractor",
    "get_extractor",
    "reset_extractor",
    # validator (A3 agent — A2 ships BASIC pathway only)
    "LayerValidator",
    "default_validator",
    # state machine
    "LayerVerdict",
    "StudentSnapshot",
    "evaluate_basic_layer",
]
