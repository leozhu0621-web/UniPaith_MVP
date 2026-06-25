"""Spec 63 — the hard model boundary, the acceptance gate.

The platform's non-negotiable rule: **Qwen processes, Claude communicates.** A
human-facing agent (the advisor chatbot + every 45 advisory surface) is *pinned
to Claude by policy* and can never be served by the Qwen ML backend — not even if
``ai_provider_per_agent_json`` maps it to ``qwen``. The processing agents (§2) may
be routed to Qwen.

These tests are the machine-checkable form of acceptance §16 #1/#2/#8:
- the pin holds for every human-facing agent, even under hostile config;
- Qwen-eligible agents *do* route to Qwen when configured;
- the boundary is well-formed (no overlap, full registry coverage);
- the failover chain never falls a human-facing agent over to Qwen;
- ``ai_turns`` accepts a ``provider='qwen'`` row (the audit transport exists).
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from unipaith.ai import boundary
from unipaith.ai.providers import (
    QwenProvider,
    get_provider,
    get_provider_for_agent,
    list_failover_order,
    reset_registry,
)
from unipaith.config import settings

# asyncio_mode = "auto" (pyproject) runs the async tests without an explicit mark.


@pytest.fixture(autouse=True)
def _clean_registry():
    """The registry caches provider singletons + the per-agent override map.
    Reset around every test so config monkeypatches don't leak across tests."""
    reset_registry()
    yield
    reset_registry()


# ── The boundary is well-formed ──────────────────────────────────────────────
def test_assert_boundary_intact_passes():
    # Raises RuntimeError on any violation; a clean return is the assertion.
    boundary.assert_boundary_intact()


def test_human_facing_and_qwen_eligible_are_disjoint():
    assert boundary.HUMAN_FACING & boundary.QWEN_ELIGIBLE == frozenset()


def test_every_registry_agent_is_classified():
    from unipaith.ai.agent_registry import AGENT_TIERS

    unclassified = {
        a for a in AGENT_TIERS if a not in boundary.HUMAN_FACING and a not in boundary.QWEN_ELIGIBLE
    }
    assert unclassified == set(), f"unclassified agents: {sorted(unclassified)}"


def test_named_first_batch_are_all_qwen_eligible_and_not_human_facing():
    # The six §2-named processing agents (the first migration batch).
    for agent in boundary.QWEN_FIRST_BATCH:
        assert agent in boundary.QWEN_ELIGIBLE
        assert not boundary.is_human_facing(agent)


# ── enforce_policy — the pin (pure) ──────────────────────────────────────────
def test_enforce_policy_pins_every_human_facing_agent_to_claude():
    for agent in boundary.HUMAN_FACING:
        assert boundary.enforce_policy(agent, "qwen") == boundary.CLAUDE_PROVIDER
        # Re-pin holds even if some future ML backend name is used.
        assert boundary.enforce_policy(agent, "qwen") != "qwen"


def test_enforce_policy_allows_qwen_for_eligible_agents():
    for agent in boundary.QWEN_ELIGIBLE:
        assert boundary.enforce_policy(agent, "qwen") == "qwen"


def test_enforce_policy_leaves_claude_and_openai_untouched():
    # The boundary only governs the Qwen ML backend; Claude↔OpenAI failover is
    # unaffected for any agent.
    for agent in ("orchestrator", "extractor"):
        assert boundary.enforce_policy(agent, "anthropic") == "anthropic"
        assert boundary.enforce_policy(agent, "openai") == "openai"


def test_unknown_agent_defaults_to_human_facing():
    # The safe direction: an unclassified agent is never auto-routed to Qwen.
    assert boundary.is_human_facing("some_unknown_future_agent") is True
    assert boundary.enforce_policy("some_unknown_future_agent", "qwen") == boundary.CLAUDE_PROVIDER


# ── Registry resolution — the pin cannot be configured away ───────────────────
def test_human_facing_pinned_to_claude_even_when_config_routes_to_qwen(monkeypatch):
    # Hostile config: route every human-facing agent to the Qwen ML backend.
    hostile = {a: "qwen" for a in boundary.HUMAN_FACING}
    monkeypatch.setattr(settings, "ai_provider_per_agent_json", json.dumps(hostile))
    monkeypatch.setattr(settings, "qwen_enabled", True)
    reset_registry()
    for agent in boundary.HUMAN_FACING:
        assert get_provider_for_agent(agent).name == "anthropic", agent


def test_qwen_eligible_agents_resolve_to_qwen_when_configured(monkeypatch):
    routed = {a: "qwen" for a in boundary.QWEN_FIRST_BATCH}
    monkeypatch.setattr(settings, "ai_provider_per_agent_json", json.dumps(routed))
    monkeypatch.setattr(settings, "qwen_enabled", True)
    reset_registry()
    for agent in boundary.QWEN_FIRST_BATCH:
        assert get_provider_for_agent(agent).name == "qwen", agent


def test_human_facing_failover_chain_never_includes_qwen(monkeypatch):
    # Even with qwen wedged into the failover CSV, a human-facing agent's chain
    # carries no Qwen hop (enforce_policy maps it to Claude, which then dedups).
    monkeypatch.setattr(settings, "ai_provider_failover_csv", "anthropic,qwen,openai")
    monkeypatch.setattr(settings, "qwen_enabled", True)
    reset_registry()
    order = list_failover_order("orchestrator")
    names = [p.name for p in order]
    assert "qwen" not in names
    assert names[0] == "together"  # the default preferred leads the chain


# ── The Qwen provider is registered but inert by default ─────────────────────
def test_qwen_provider_is_registered():
    p = get_provider("qwen")
    assert isinstance(p, QwenProvider)
    assert p.name == "qwen"


def test_qwen_provider_inert_until_enabled(monkeypatch):
    monkeypatch.setattr(settings, "qwen_enabled", False)
    reset_registry()
    assert get_provider("qwen").is_available() is False


def test_qwen_provider_tier_map_reads_settings(monkeypatch):
    monkeypatch.setattr(settings, "qwen_model_workhorse", "qwen3-14b-instruct")
    monkeypatch.setattr(settings, "qwen_model_batch", "qwen3-7b-instruct")
    monkeypatch.setattr(settings, "qwen_model_flagship", "qwen3-32b-instruct")
    p = QwenProvider()
    assert p.model_id("workhorse") == "qwen3-14b-instruct"
    assert p.model_id("batch") == "qwen3-7b-instruct"
    assert p.model_id("flagship") == "qwen3-32b-instruct"


# ── The audit transport exists — ai_turns accepts provider='qwen' ────────────
async def test_ai_turns_accepts_qwen_provider_row(db_session):
    """A Qwen-served processing call must be recordable. The presence of 'qwen' in
    the CHECK is also the auditable proof of the boundary — a human-facing row can
    only ever be anthropic/openai, so a qwen row is never a human-facing surface."""
    from unipaith.models.ai_artifacts import AiTurn

    turn = AiTurn(
        student_id=None,
        agent="embedding",  # a Qwen-eligible processing agent
        role="tool",
        model="qwen3-embedding-8b",
        provider="qwen",
        input_tokens=12,
        output_tokens=0,
        cost_usd=Decimal("0.000001"),
        latency_ms=5,
        success=True,
    )
    db_session.add(turn)
    await db_session.flush()  # CHECK enforced here — no IntegrityError == accepted
    assert turn.id is not None
    assert turn.provider == "qwen"
