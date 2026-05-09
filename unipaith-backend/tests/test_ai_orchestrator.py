"""Phase A2 — Orchestrator unit tests.

Mock-mode coverage. Real-mode framework-adherence grading lives in
`ai.evals.runner.run_framework_adherence(real=True)`.
"""

from __future__ import annotations

import asyncio

from unipaith.ai.client import AIClient
from unipaith.ai.orchestrator import (
    Orchestrator,
    TurnContext,
    get_orchestrator,
    reset_orchestrator,
)
from unipaith.ai.state import StudentSnapshot, evaluate_basic_layer


def _mock_client() -> AIClient:
    return AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )


def test_orchestrator_singleton_pattern() -> None:
    reset_orchestrator()
    a = get_orchestrator()
    b = get_orchestrator()
    assert a is b
    reset_orchestrator()
    c = get_orchestrator()
    assert c is not a


def test_state_header_renders_known_state() -> None:
    """The state header must include track, layer, completion %, missing
    signals, and the next probe — these are the orchestrator's grounding."""
    snap = StudentSnapshot(age=20, education_level="bachelors")
    verdict = evaluate_basic_layer(snap)
    ctx = TurnContext(
        track="profile",
        layer="basic",
        completion_pct=0.40,
        verdict=verdict,
        known_profile_summary="- age: 20\n- education_level: bachelors",
    )
    header = Orchestrator._render_state_header(ctx)
    assert "Track: profile" in header
    assert "Layer: basic" in header
    assert "40%" in header
    assert verdict.next_probe_hint is not None
    assert verdict.next_probe_hint[:20] in header


def test_state_header_handles_no_verdict() -> None:
    """First turn — no verdict yet. Header still renders."""
    ctx = TurnContext(
        track="profile",
        layer="basic",
        completion_pct=0.0,
        verdict=None,
        known_profile_summary="",
    )
    header = Orchestrator._render_state_header(ctx)
    assert "(none — pick the next probe yourself" in header
    assert "(nothing yet)" in header


def test_build_messages_first_turn_synthetic_kickoff() -> None:
    """Anthropic requires a non-empty messages array. With no history we
    inject a synthetic 'session starting' user turn."""
    ctx = TurnContext(
        track="profile",
        layer="basic",
        completion_pct=0.0,
        verdict=None,
        known_profile_summary="",
    )
    msgs = Orchestrator._build_messages(ctx)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"


def test_build_messages_passes_history_through() -> None:
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hey — let's start with where you are in school."},
        {"role": "user", "content": "Senior at Binghamton."},
    ]
    ctx = TurnContext(
        track="profile",
        layer="basic",
        completion_pct=0.0,
        verdict=None,
        known_profile_summary="",
        history=history,
    )
    msgs = Orchestrator._build_messages(ctx)
    assert msgs == history


def test_parse_response_extracts_text_and_tool_calls() -> None:
    """The orchestrator's parser must surface text, record_artifact calls,
    and the layer-advance signal as separate fields."""
    orch = Orchestrator(client=_mock_client())

    class _StubResponse:
        cost_usd = 0.0
        latency_ms = 42
        content_blocks = [
            {"type": "text", "text": "Got it — let's keep going.\n"},
            {
                "type": "tool_use",
                "name": "record_artifact",
                "input": {"type": "basic_field", "value": {"age": 20}, "evidence": "I'm 20"},
            },
            {
                "type": "tool_use",
                "name": "request_layer_advance",
                "input": {"rationale": "all five fields present"},
            },
        ]

    response = orch._parse_response(_StubResponse())
    assert response.text == "Got it — let's keep going."
    assert len(response.record_artifact_calls) == 1
    assert response.record_artifact_calls[0]["type"] == "basic_field"
    assert response.requested_layer_advance is True
    assert response.advance_rationale == "all five fields present"
    assert response.latency_ms == 42


def test_parse_response_text_only() -> None:
    """Most turns won't have tool calls. Parser must handle that cleanly."""
    orch = Orchestrator(client=_mock_client())

    class _StubResponse:
        cost_usd = 0.001
        latency_ms = 800
        content_blocks = [{"type": "text", "text": "Tell me about your hometown."}]

    response = orch._parse_response(_StubResponse())
    assert response.text == "Tell me about your hometown."
    assert response.record_artifact_calls == []
    assert response.requested_layer_advance is False


def test_respond_in_mock_mode_returns_orchestrator_response() -> None:
    """Smoke test: the full call path runs in mock mode without errors.
    The mock client returns a canned text-only response; we verify the
    orchestrator wraps it correctly."""
    orch = Orchestrator(client=_mock_client())
    ctx = TurnContext(
        track="profile",
        layer="basic",
        completion_pct=0.0,
        verdict=None,
        known_profile_summary="",
    )
    response = asyncio.run(orch.respond(ctx=ctx))
    assert response.text.startswith("[mock:orchestrator")
    assert response.requested_layer_advance is False
