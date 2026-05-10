"""UniPaith AI package.

Phase progression
-----------------
- A1 (shipped): Anthropic client wrapper, prompt files, extractor schema,
  eval harness, DB foundations.
- A2 (shipped): Discovery BASIC layer end-to-end — Orchestrator +
  Extractor + (deterministic BASIC) Validator + artifact-writer.
- A3 (shipped): Personality + Identity layers, LLM-as-judge,
  bias-pair fixtures.
- A3.2 (shipped): SSE streaming, GOALS + NEEDS tracks, Haiku judge for
  soft criteria.
- B1 (this phase): Feature Emitter (A4) + ML matcher (fitness +
  confidence + components, with hard-filter rule layer).
- B+: Rationale agent (A5), workshop coaches (A6).

All LLM calls in the application MUST go through `unipaith.ai.client.AIClient`.
This is enforced by:
  - the cost ledger (`ai_turns` table) — every call writes a row
  - the per-student cost cap — checked before each call
  - the prompt-cache layout — built into the client, not duplicated per agent

External code imports either the client singleton (low-level) or one of the
agent singletons (high-level):

    from unipaith.ai import get_client, get_orchestrator, get_extractor,
                            get_feature_emitter
"""

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.coach import (
    CoachFeedback,
    CoachResult,
    EssayDraft,
    InterviewCoachResult,
    InterviewFeedback,
    InterviewResponse,
    JudgeVerdict,
    TestPrepCoachResult,
    TestPrepContext,
    TestPrepFeedback,
    WorkshopCoach,
    get_workshop_coach,
    reset_workshop_coach,
)
from unipaith.ai.extractor import (
    ExtractedSignals,
    Extractor,
    get_extractor,
    reset_extractor,
)
from unipaith.ai.feature_emitter import (
    EmittedFeatures,
    FeatureEmitter,
    get_feature_emitter,
    persist_features,
    reset_feature_emitter,
)
from unipaith.ai.orchestrator import (
    Orchestrator,
    OrchestratorResponse,
    TurnContext,
    get_orchestrator,
    reset_orchestrator,
)
from unipaith.ai.rationale import (
    ProgramView,
    RationaleAgent,
    RationaleResult,
    ScoreView,
    StudentView,
    get_rationale_agent,
    is_grounded,
    reset_rationale_agent,
    resolve_path,
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
    # validator (A3 agent)
    "LayerValidator",
    "default_validator",
    # feature emitter (A4 agent — Phase B1)
    "EmittedFeatures",
    "FeatureEmitter",
    "get_feature_emitter",
    "persist_features",
    "reset_feature_emitter",
    # rationale (A5 agent — Phase B2)
    "RationaleAgent",
    "RationaleResult",
    "StudentView",
    "ProgramView",
    "ScoreView",
    "get_rationale_agent",
    "reset_rationale_agent",
    "is_grounded",
    "resolve_path",
    # workshop coach (A6 agent — Phase C1)
    "WorkshopCoach",
    "CoachFeedback",
    "CoachResult",
    "EssayDraft",
    "JudgeVerdict",
    # Phase C2: interview + test-prep
    "InterviewResponse",
    "InterviewFeedback",
    "InterviewCoachResult",
    "TestPrepContext",
    "TestPrepFeedback",
    "TestPrepCoachResult",
    "get_workshop_coach",
    "reset_workshop_coach",
    # state machine
    "LayerVerdict",
    "StudentSnapshot",
    "evaluate_basic_layer",
]
