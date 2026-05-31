"""Spec 03 §14 — runtime compliance checklist.

One test per checklist item from `Spec/03-llm-claude-migration.md` §14.
Each test is structural — it verifies the building block exists and
behaves correctly in mock mode. End-to-end provider+ledger behavior is
covered by `test_ai_client.py` and the integration tests; this file is
the single place to grep when verifying spec coverage.
"""

from __future__ import annotations

import json

import pytest

from unipaith.ai.cache_invalidation import (
    RATIONALE_PROMPT_VERSION,
)
from unipaith.ai.client import (
    MODEL_PRICES,
    AIClient,
    AllProvidersFailedError,
    ConsentDeniedError,
)
from unipaith.ai.consent import (
    AGENT_REQUIRES,
    DEFAULT_MASK,
    get_consent_mask,
    is_call_permitted,
)
from unipaith.ai.providers import (
    AnthropicProvider,
    OpenAIProvider,
    get_provider,
    list_failover_order,
    reset_registry,
)
from unipaith.ai.providers.base import AIProvider, ChatRequest, ChatResponse, Tier
from unipaith.config import settings

# ── §14 checklist item 1: provider selected via env, never hardcoded ────


def test_provider_default_is_env_driven():
    """`AI_PROVIDER_DEFAULT=anthropic` is the configured default."""
    assert settings.ai_provider_default == "anthropic"


def test_anthropic_provider_registered_under_name():
    reset_registry()
    p = get_provider("anthropic")
    assert isinstance(p, AnthropicProvider)
    assert p.name == "anthropic"


def test_openai_provider_registered_under_name():
    reset_registry()
    p = get_provider("openai")
    assert isinstance(p, OpenAIProvider)
    assert p.name == "openai"


def test_rule_based_is_not_a_real_provider():
    """rule_based is a sentinel — instantiation must fail loudly so the
    AIClient is forced to short-circuit to the agent-specific fallback."""
    reset_registry()
    with pytest.raises(ValueError, match="rule_based"):
        get_provider("rule_based")


# ── §14 checklist item 2: cache layout (1h system, 5min persona, tail) ──


def test_chat_request_carries_cache_layout_metadata():
    """The request object exposes `cache_control_layout` so providers
    can choose to emit the right beta header. AIClient sets the
    default to `system_1h+persona_5min+tail` per spec §3."""
    req = ChatRequest(tier="workhorse", system="x", messages=[])
    assert req.cache_control_layout == "system_1h+persona_5min+tail"


# ── §14 checklist item 3: consent_mask resolved before call + recorded ─


def test_default_mask_has_all_four_keys():
    """Spec 03 §11 requires four keys: matching, outreach, analytics, training."""
    assert set(DEFAULT_MASK.keys()) == {"matching", "outreach", "analytics", "training"}


def test_each_agent_declares_consent_requirement():
    """Every agent name listed on `AiTurn.agent` CHECK constraint also
    appears in AGENT_REQUIRES so the consent gate has an answer for it.

    Spec 06 §2 added review_summarizer (Opus) + authenticity_risk (Haiku) +
    the L3 'matcher' audit label; all are declared in AGENT_REQUIRES.
    """
    expected_agents = {
        "orchestrator",
        "extractor",
        "validator",
        "feature_emitter",
        "rationale",
        "workshop_coach",
        "workshop_judge",
        "embedding",
        # Spec 06 §2 additions.
        "review_summarizer",
        "authenticity_risk",
        "matcher",
        # Spec 10 §3 / 45 §12 — type-first search query interpreter.
        "query_interpreter",
    }
    assert set(AGENT_REQUIRES.keys()) == expected_agents


def test_matching_consent_blocks_rationale_agent():
    mask = {"matching": False, "outreach": True, "analytics": True, "training": True}
    assert is_call_permitted("rationale", mask) is False
    assert is_call_permitted("feature_emitter", mask) is False
    assert is_call_permitted("embedding", mask) is False


def test_analytics_consent_blocks_extractor():
    mask = {"matching": True, "outreach": True, "analytics": False, "training": True}
    assert is_call_permitted("extractor", mask) is False
    assert is_call_permitted("validator", mask) is False


def test_workshop_coach_runs_regardless_of_mask():
    """Workshop coaches are user-initiated artifact work — entry IS
    the consent signal."""
    fully_denied = {k: False for k in DEFAULT_MASK}
    assert is_call_permitted("workshop_coach", fully_denied) is True


async def test_get_consent_mask_returns_default_for_no_student(monkeypatch):
    mask = await get_consent_mask(db=None, student_id=None)
    assert mask == DEFAULT_MASK


@pytest.mark.asyncio
async def test_consent_denied_raises_for_matching_agent(monkeypatch):
    """In mock mode + with a denying consent mask, the AIClient must
    raise ConsentDeniedError BEFORE attempting any provider call."""
    import unipaith.ai.client as client_mod

    async def fake_mask(db, student_id):
        return {
            "matching": False,
            "outreach": True,
            "analytics": True,
            "training": True,
        }

    monkeypatch.setattr(client_mod, "get_consent_mask", fake_mask)

    client = AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )
    import uuid as _uuid

    with pytest.raises(ConsentDeniedError) as exc:
        await client.message(
            agent="rationale",
            model="sonnet",
            system="x",
            messages=[{"role": "user", "content": "y"}],
            student_id=_uuid.uuid4(),
        )
    assert exc.value.denied_mask_key == "matching"


# ── §14 checklist item 4: audit ledger row written with required fields ─


def test_ai_turn_model_has_spec_03_fields():
    """The AiTurn ORM mapping carries provider, success, failure_reason,
    consent_mask, request_started_at, request_completed_at."""
    from unipaith.models.ai_artifacts import AiTurn

    cols = {c.name for c in AiTurn.__table__.columns}
    required = {
        "provider",
        "success",
        "failure_reason",
        "consent_mask",
        "request_started_at",
        "request_completed_at",
    }
    missing = required - cols
    assert not missing, f"AiTurn is missing spec 03 columns: {missing}"


def test_ai_turn_provider_check_constraint_exists():
    from unipaith.models.ai_artifacts import AiTurn

    check_names = {c.name for c in AiTurn.__table__.constraints if hasattr(c, "name") and c.name}
    assert "ck_ai_turns_provider" in check_names
    assert "ck_ai_turns_failure_reason" in check_names


# ── §14 checklist item 5: rule-based fallback registered ────────────────


def test_all_providers_failed_error_carries_attempts():
    err = AllProvidersFailedError(agent="rationale", attempts=3)
    assert err.agent == "rationale"
    assert err.attempts == 3


# ── §14 checklist item 6: failover via AI_PROVIDER_FAILOVER ─────────────


def test_failover_csv_parses_to_ordered_providers(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider_failover_csv", "anthropic,openai")
    reset_registry()
    order = list_failover_order(agent="rationale")
    names = [p.name for p in order]
    # First slot is the agent's preferred provider (default anthropic).
    assert names[0] == "anthropic"
    # Failover provider only appears when it's actually available; in
    # CI with no OPENAI_API_KEY this is filtered out (correct per spec
    # so we don't burn a hop on a known no-op).
    assert "rule_based" not in names


def test_failover_skips_unknown_providers(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider_failover_csv", "anthropic,not_a_provider,openai")
    reset_registry()
    order = list_failover_order(agent="rationale")
    names = [p.name for p in order]
    assert "not_a_provider" not in names


def test_per_agent_override_takes_precedence(monkeypatch):
    monkeypatch.setattr(
        settings,
        "ai_provider_per_agent_json",
        json.dumps({"rationale": "openai"}),
    )
    monkeypatch.setattr(settings, "openai_api_key", "stub-for-availability")
    reset_registry()
    order = list_failover_order(agent="rationale")
    # rationale was overridden to openai → it leads even though
    # anthropic is the global default.
    assert order[0].name == "openai"


# ── §14 checklist item 7: no model older than the most recent 4.x ───────


def test_model_prices_includes_flagship_opus_4_8():
    """Spec 03 §2: flagship tier must point at Opus 4.8 minimum."""
    assert "claude-opus-4-8" in MODEL_PRICES
    assert MODEL_PRICES["claude-opus-4-8"]["input"] == 15.00
    assert MODEL_PRICES["claude-opus-4-8"]["output"] == 75.00


def test_model_prices_includes_workhorse_sonnet_4_6():
    assert "claude-sonnet-4-6" in MODEL_PRICES


def test_model_prices_includes_batch_haiku_4_5():
    assert "claude-haiku-4-5-20251001" in MODEL_PRICES


def test_default_tier_map_matches_spec_2():
    """Spec 03 §2: tier mapping is flagship=Opus, workhorse=Sonnet,
    batch=Haiku."""
    assert settings.anthropic_default_flagship == "claude-opus-4-8"
    assert settings.anthropic_default_workhorse == "claude-sonnet-4-6"
    assert settings.anthropic_default_batch == "claude-haiku-4-5-20251001"


# ── §14 checklist item 8: output schema validation runs ─────────────────
# Covered by per-agent tests (test_ai_extractor.py validates the
# ExtractedSignals schema; test_ai_rationale.py validates RationaleResult).


# ── §14 checklist item 9: AI_MOCK_MODE short-circuits before network IO ─


def test_mock_mode_does_not_require_api_key():
    client = AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )
    # Mock client must instantiate without throwing.
    assert client.mock_mode is True
    # No SDK should have been touched yet — lazy-init.
    assert client._anthropic is None
    assert client._voyage is None


# ── §14 checklist item 10: tokens/cost reported to dashboard ────────────
# Covered structurally — `AiTurn.cost_usd` is the source column.


def test_cost_dashboard_columns_present():
    from unipaith.models.ai_artifacts import AiTurn

    cols = {c.name for c in AiTurn.__table__.columns}
    required = {
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_creation_tokens",
        "cost_usd",
        "latency_ms",
        "agent",
        "provider",
        "success",
    }
    missing = required - cols
    assert not missing, f"Cost dashboard columns missing: {missing}"


# ── Spec 03 §12 — cache invalidation on consent change ──────────────────


def test_rationale_prompt_version_is_int():
    assert isinstance(RATIONALE_PROMPT_VERSION, int)
    assert RATIONALE_PROMPT_VERSION >= 1


def test_match_rationale_pk_includes_prompt_version():
    """Spec 03 §12: prompt_version is part of the composite PK so a
    prompt iteration forces re-derivation."""
    from unipaith.models.ai_artifacts import MatchRationale

    pk_cols = [c.name for c in MatchRationale.__table__.primary_key]
    assert "prompt_version" in pk_cols
    assert "profile_version" in pk_cols
    assert "program_version" in pk_cols


# ── Spec 03 §9 — failover behavior with a mock provider that fails ──────


class _AlwaysFailsProvider(AIProvider):
    name = "always_fails"

    def __init__(self, exception: Exception):
        self._exception = exception
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    def model_id(self, tier: Tier) -> str:
        return f"failtest:{tier}"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        self.call_count += 1
        raise self._exception


def test_provider_protocol_runtime_checkable():
    """The Protocol is @runtime_checkable so registry can isinstance-check."""
    p = _AlwaysFailsProvider(exception=RuntimeError("boom"))
    assert isinstance(p, AIProvider)


# ── Spec 03 §3/§14 — prompt-cache TTL layout (system 1h, tail uncached) ──


def test_prompt_cache_markers_match_spec_3():
    """CACHE_1H is the 1-hour system breakpoint; CACHE_5MIN is the default
    ephemeral persona marker (no ttl == 5 minutes)."""
    from unipaith.ai.prompt_cache import CACHE_1H, CACHE_5MIN

    assert CACHE_1H == {"type": "ephemeral", "ttl": "1h"}
    assert CACHE_5MIN == {"type": "ephemeral"}


def test_orchestrator_caches_system_block_at_1h():
    """Spec 03 §3/§14: the long system prompt is the highest-leverage
    breakpoint and must be cached at 1h; the per-turn state header is the
    uncached tail."""
    from unipaith.ai.orchestrator import Orchestrator, TurnContext

    orch = Orchestrator(system_prompt="SYSTEM PROMPT TEXT")
    ctx = TurnContext(
        track="profile",
        layer=None,
        completion_pct=0.0,
        verdict=None,
        known_profile_summary="",
    )
    blocks = orch._build_system_blocks(ctx)
    # Block 0 = system prompt, cached at 1h.
    assert blocks[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    # Block 1 = volatile per-turn state header, uncached (the tail).
    assert "cache_control" not in blocks[1]


def test_no_production_agent_caches_system_at_5min():
    """Guard against regression: every production agent module marks its
    cacheable system/tool blocks with the named CACHE_1H constant, never a
    bare 5-minute ephemeral dict. The eval harness is exempt (its criteria
    vary per case, so 5min is correct there)."""
    import pathlib

    ai_dir = pathlib.Path(__file__).resolve().parent.parent / "src" / "unipaith" / "ai"
    production_agents = [
        "orchestrator.py",
        "extractor.py",
        "validator.py",
        "feature_emitter.py",
        "rationale.py",
        "coach.py",
        "strategy.py",
        "identity.py",
    ]
    offenders = []
    for name in production_agents:
        text = (ai_dir / name).read_text(encoding="utf-8")
        if '"cache_control": {"type": "ephemeral"}' in text:
            offenders.append(name)
    assert not offenders, f"Agents still use a bare 5-min cache marker: {offenders}"


# ── Spec 03 §8/§13 — migration chain integrity (single head for deploys) ─


def test_alembic_has_single_head():
    """`alembic upgrade head` is unambiguous only with one head. A second
    head silently breaks deploys, so pin it here."""
    import pathlib

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    backend_root = pathlib.Path(__file__).resolve().parent.parent
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected exactly one alembic head, found {len(heads)}: {heads}"
