"""Open-weight provider (Qwen via Together AI) — the migration target.

Covers the provider in isolation (name, availability, tier→model, pricing, a
mocked forced-tool round-trip) plus its registry wiring and the cutover routing
topology: `opensource` serves every agent (no boundary pin against it, unlike the
self-hosted `qwen` vLLM transport), and an `opensource`-only failover chain has no
Claude in it — the rule-based path is the only net.

See `OPEN_MODEL_MIGRATION_PLAN.md` / `CLAUDE_CODE_TASK_qwen_migration.md`.
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.ai.providers import (
    OpenSourceProvider,
    get_provider,
    get_provider_for_agent,
    list_failover_order,
    reset_registry,
)
from unipaith.ai.providers.base import ChatRequest
from unipaith.config import settings

# asyncio_mode = "auto" (pyproject) runs the async tests without an explicit mark.

# A non-empty placeholder so is_available() passes its key check — not a real
# credential (referenced by name so the secret scanner doesn't flag a literal).
_FILLED = "not-a-real-key"  # noqa: S105


# ── Fake AsyncOpenAI SDK — returns a forced tool_use response ─────────────────
class _FakeFn:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class _FakeToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.function = _FakeFn(name, arguments)


class _FakeMessage:
    def __init__(self, content, tool_calls):
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, message, finish_reason):
        self.message = message
        self.finish_reason = finish_reason


class _FakeUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _FakeResponse:
    def __init__(self, choices, usage):
        self.choices = choices
        self.usage = usage


class _FakeCompletions:
    def __init__(self, response):
        self._response = response
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._response


class _FakeChat:
    def __init__(self, completions):
        self.completions = completions


class _FakeSDK:
    def __init__(self, response):
        self.chat = _FakeChat(_FakeCompletions(response))


def _forced_tool_response(*, tool_name="emit_rationale", args='{"summary": "strong fit"}'):
    return _FakeResponse(
        choices=[
            _FakeChoice(
                message=_FakeMessage(
                    content="",
                    tool_calls=[_FakeToolCall(id="call_1", name=tool_name, arguments=args)],
                ),
                finish_reason="tool_calls",
            )
        ],
        usage=_FakeUsage(prompt_tokens=100, completion_tokens=20),
    )


# ── Identity ──────────────────────────────────────────────────────────────────
def test_provider_name_is_opensource():
    assert OpenSourceProvider().name == "opensource"


def test_init_reads_together_base_url_from_settings():
    p = OpenSourceProvider()
    assert p.base_url == settings.opensource_base_url == "https://api.together.xyz/v1"


# ── Availability ──────────────────────────────────────────────────────────────
def test_is_available_false_without_key():
    assert OpenSourceProvider(api_key="").is_available() is False


def test_is_available_true_with_key():
    # The openai SDK is installed (Together is OpenAI-compatible) → a key is the
    # only thing gating availability.
    assert OpenSourceProvider(api_key=_FILLED).is_available() is True


# ── Tier → Qwen model ─────────────────────────────────────────────────────────
def test_model_id_maps_each_tier_to_a_qwen_model():
    p = OpenSourceProvider()
    assert p.model_id("flagship") == settings.opensource_flagship == "Qwen/Qwen3-235B-A22B-Instruct"
    assert p.model_id("workhorse") == settings.opensource_workhorse == "Qwen/Qwen3-30B-A3B-Instruct"
    assert p.model_id("batch") == settings.opensource_batch == "Qwen/Qwen3-8B"


def test_model_id_tracks_settings_overrides(monkeypatch):
    monkeypatch.setattr(settings, "opensource_workhorse", "Qwen/Qwen3-Custom")
    assert OpenSourceProvider().model_id("workhorse") == "Qwen/Qwen3-Custom"


# ── Pricing ───────────────────────────────────────────────────────────────────
def test_compute_cost_known_model():
    # workhorse Qwen3-30B-A3B: input 0.20, output 0.60 per MTok.
    cost = OpenSourceProvider._compute_cost(
        model_id="Qwen/Qwen3-30B-A3B-Instruct",
        input_tokens=100,
        output_tokens=20,
    )
    assert cost == Decimal("0.000032")  # 100/1e6*0.20 + 20/1e6*0.60


def test_compute_cost_unknown_model_is_zero():
    cost = OpenSourceProvider._compute_cost(
        model_id="some/unlisted-model",
        input_tokens=1000,
        output_tokens=1000,
    )
    assert cost == Decimal("0")


# ── Forced-tool round-trip (structured output for rationale/strategy/…) ────────
async def test_chat_returns_forced_tool_use_block():
    provider = OpenSourceProvider(api_key=_FILLED)
    provider._sdk = _FakeSDK(_forced_tool_response())  # bypass the real SDK
    req = ChatRequest(
        tier="workhorse",
        system="You are a counselor.",
        messages=[{"role": "user", "content": "explain this match"}],
        tools=[
            {
                "name": "emit_rationale",
                "description": "Emit the structured rationale.",
                "input_schema": {"type": "object", "properties": {"summary": {"type": "string"}}},
            }
        ],
        tool_choice={"type": "tool", "name": "emit_rationale"},
    )

    out = await provider.chat(req)

    # The response is normalized to Anthropic-shape tool_use so AIClient consumers
    # parse it identically across providers.
    tool_uses = [b for b in out.content_blocks if b["type"] == "tool_use"]
    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "emit_rationale"
    assert tool_uses[0]["input"] == {"summary": "strong fit"}

    assert out.provider == "opensource"
    assert out.model == settings.opensource_workhorse
    assert out.input_tokens == 100
    assert out.output_tokens == 20
    assert out.cost_usd == Decimal("0.000032")


async def test_chat_forwards_forced_tool_choice_to_together():
    # The forced tool_choice must reach Together as OpenAI function-calling so Qwen
    # reliably returns parseable args (brief §4 structured output).
    provider = OpenSourceProvider(api_key=_FILLED)
    fake = _FakeSDK(_forced_tool_response())
    provider._sdk = fake
    req = ChatRequest(
        tier="flagship",
        system="sys",
        messages=[{"role": "user", "content": "go"}],
        tools=[{"name": "emit_rationale", "description": "d", "input_schema": {"type": "object"}}],
        tool_choice={"type": "tool", "name": "emit_rationale"},
    )

    await provider.chat(req)

    sent = fake.chat.completions.calls[0]
    assert sent["model"] == settings.opensource_flagship
    assert sent["tools"][0]["type"] == "function"
    assert sent["tools"][0]["function"]["name"] == "emit_rationale"
    assert sent["tool_choice"] == {"type": "function", "function": {"name": "emit_rationale"}}


# ── Registry wiring ───────────────────────────────────────────────────────────
def test_opensource_registered_under_name():
    reset_registry()
    p = get_provider("opensource")
    assert isinstance(p, OpenSourceProvider)
    assert p.name == "opensource"


def test_opensource_serves_human_facing_agents(monkeypatch):
    # Founder decision (2026-06-25): the open-weight provider is the home for
    # EVERY agent — there is no boundary pin against `opensource` (unlike the
    # self-hosted `qwen` vLLM transport, which stays pinned away from human-facing
    # agents). A human-facing agent routed to opensource resolves to opensource,
    # not bounced to Claude.
    monkeypatch.setattr(settings, "ai_provider_default", "opensource")
    reset_registry()
    for agent in ("orchestrator", "rationale", "strategy"):
        assert get_provider_for_agent(agent).name == "opensource", agent


def test_opensource_only_chain_has_no_claude_then_rule_based(monkeypatch):
    # The cutover topology: opensource is the single provider, rule-based is the
    # only net. With the key unset, opensource is the (unavailable) preferred — the
    # chain carries no Claude/OpenAI hop; the AIClient runs rule-based after it.
    monkeypatch.setattr(settings, "ai_provider_default", "opensource")
    monkeypatch.setattr(settings, "ai_provider_failover_csv", "opensource")
    monkeypatch.setattr(settings, "opensource_api_key", "")
    reset_registry()
    order = list_failover_order(agent="rationale")
    names = [p.name for p in order]
    assert names == ["opensource"]  # preferred kept even when unavailable
    assert "anthropic" not in names and "openai" not in names  # Claude removed
    assert "rule_based" not in names  # sentinel — run by the caller after exhaustion
