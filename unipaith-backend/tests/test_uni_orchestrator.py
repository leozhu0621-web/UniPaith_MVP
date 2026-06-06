"""Uni counselor — system prompt + track-less discovery mode (Plan tasks 1-2)."""

from __future__ import annotations

from unipaith.ai.orchestrator import _DISCOVERY_SYSTEM_PROMPT


def test_system_prompt_includes_uni_playbook() -> None:
    p = _DISCOVERY_SYSTEM_PROMPT.lower()
    assert "uni" in p  # persona named
    assert "one question" in p or "more than one" in p  # one-question-per-turn rule
    assert "reflect" in p  # active listening
    assert "slang" in p  # no-slang rule present
