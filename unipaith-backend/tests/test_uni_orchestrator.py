"""Uni counselor — system prompt + track-less discovery mode (Plan tasks 1-2)."""

from __future__ import annotations

from unipaith.ai.orchestrator import _DISCOVERY_SYSTEM_PROMPT, Orchestrator, TurnContext


def test_system_prompt_includes_uni_playbook() -> None:
    p = _DISCOVERY_SYSTEM_PROMPT.lower()
    assert "uni" in p  # persona named
    assert "one question" in p or "more than one" in p  # one-question-per-turn rule
    assert "reflect" in p  # active listening
    assert "slang" in p  # no-slang rule present


def test_state_header_unified_discovery_is_trackless() -> None:
    ctx = TurnContext(
        track="discovery",
        layer=None,
        completion_pct=0.0,
        verdict=None,
        known_profile_summary="",
    )
    header = Orchestrator._render_state_header(ctx)
    assert "open discovery conversation" in header.lower()
    assert "- Track:" not in header  # no track menu pushed at the model
    assert "other tracks" not in header.lower()
