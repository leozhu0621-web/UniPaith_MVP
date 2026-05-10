"""Phase D — Haiku-as-judge in the framework_adherence eval suite.

The judge sits inside `_run_framework_adherence_real` and was previously
covering only three named criteria. This PR expanded its coverage to all
soft must_do / must_not_do behaviors that the deterministic structural
pass can't reliably detect.

These tests stub the Anthropic call so we exercise the wiring (criteria
generation, response parsing, per-criterion accumulation) without
burning tokens or requiring an API key.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

import pytest

from unipaith.ai import evals as evals_pkg
from unipaith.ai.client import LLMResponse
from unipaith.ai.evals import runner as runner_mod


def _make_judge_response(scores: list[dict[str, Any]]) -> LLMResponse:
    """Build an LLMResponse whose only content_block is a tool_use carrying
    the score schema the judge expects."""
    return LLMResponse(
        text="",
        content_blocks=[
            {
                "type": "tool_use",
                "id": "tu_test",
                "name": "score_soft_criteria",
                "input": {"scores": scores},
            }
        ],
        model="mock:claude-haiku-4-5",
        cost_usd=Decimal("0"),
    )


class _StubOrchestratorResponse:
    """Stand-in for OrchestrationResponse — only needs .text for the
    structural pass + the judge's payload."""

    def __init__(self, text: str):
        self.text = text


class _StubOrchestrator:
    def __init__(self, reply: str = "Tell me about your goals."):
        self.reply = reply

    async def respond(self, *, ctx, **kwargs):  # noqa: ARG002
        return _StubOrchestratorResponse(self.reply)


class _StubClient:
    """Records every judge call so we can assert what criteria were sent."""

    def __init__(self, scores_for_each_call: list[list[dict[str, Any]]]):
        self.calls: list[dict[str, Any]] = []
        self._queue = list(scores_for_each_call)

    async def message(self, **kwargs):
        self.calls.append(kwargs)
        scores = self._queue.pop(0) if self._queue else []
        return _make_judge_response(scores)


def _patch_real_mode(
    monkeypatch: pytest.MonkeyPatch,
    *,
    judge_scores: list[list[dict[str, Any]]],
    orch_reply: str = "Tell me about your goals.",
):
    """Wire the stubs into the runner module."""

    stub_client = _StubClient(judge_scores)
    stub_orch = _StubOrchestrator(orch_reply)

    def _get_client_stub():
        return stub_client

    def _get_orchestrator_stub():
        return stub_orch

    # Patch the module-level `get_client` / `get_orchestrator` imports
    # the function uses at call time (they're imported inside the
    # function body, so we patch the source modules).
    import unipaith.ai.client as client_mod
    import unipaith.ai.orchestrator as orch_mod

    monkeypatch.setattr(client_mod, "get_client", _get_client_stub)
    monkeypatch.setattr(orch_mod, "get_orchestrator", _get_orchestrator_stub)
    return stub_client, stub_orch


# ── Criteria coverage ─────────────────────────────────────────────────────


def test_judge_covers_expanded_must_do_criteria(
    monkeypatch: pytest.MonkeyPatch,
):
    """The expanded set of soft must_do criteria should all be sent to
    the judge. Probe with an expectation that lists every one and assert
    the payload contains them."""
    judge_scores = [
        [
            {"name": "acknowledge_emotion_specifically", "passed": True, "reason": "x"},
            {"name": "redirect_to_discovery", "passed": True, "reason": "x"},
            {"name": "ask_basic_layer_question", "passed": True, "reason": "x"},
            {"name": "probe_identity_or_personality", "passed": True, "reason": "x"},
            {"name": "reflect_value_back", "passed": True, "reason": "x"},
            {"name": "name_specific_strength", "passed": True, "reason": "x"},
        ]
    ]
    stub_client, _ = _patch_real_mode(monkeypatch, judge_scores=judge_scores)

    conv = {
        "id": "synth",
        "scripted_user_turns": ["hi"],
        "expectations": [
            {
                "turn_index": 0,
                "must_do": [
                    "acknowledge_emotion_specifically",
                    "redirect_to_discovery",
                    "ask_basic_layer_question",
                    "probe_identity_or_personality",
                    "reflect_value_back",
                    "name_specific_strength",
                ],
            }
        ],
    }
    result = runner_mod._run_framework_adherence_real([conv])
    # Judge was called exactly once.
    assert len(stub_client.calls) == 1
    # The payload sent to the judge enumerates all criteria.
    payload = stub_client.calls[0]["messages"][0]["content"]
    for name in (
        "acknowledge_emotion_specifically",
        "redirect_to_discovery",
        "ask_basic_layer_question",
        "probe_identity_or_personality",
        "reflect_value_back",
        "name_specific_strength",
    ):
        assert f'"name": "{name}"' in payload, f"criterion {name!r} missing from payload"
    # Per-criterion stats are surfaced in the detail block.
    for name in (
        "acknowledge_emotion_specifically",
        "ask_basic_layer_question",
        "probe_identity_or_personality",
    ):
        assert result.detail["soft_criteria"][name] == {"passed": 1, "total": 1}


def test_judge_covers_must_not_do_soft_criteria(
    monkeypatch: pytest.MonkeyPatch,
):
    """Soft must_not_do entries should be sent to the judge prefixed
    with `not:` so the verdict layer can tell which behavior was
    inverted."""
    judge_scores = [
        [
            {"name": "not:recommend_program", "passed": True, "reason": "x"},
            {"name": "not:premature_advice", "passed": True, "reason": "x"},
            {"name": "not:discount_emotion", "passed": True, "reason": "x"},
        ]
    ]
    stub_client, _ = _patch_real_mode(monkeypatch, judge_scores=judge_scores)

    conv = {
        "id": "synth",
        "scripted_user_turns": ["hi"],
        "expectations": [
            {
                "turn_index": 0,
                "must_not_do": [
                    "recommend_program",
                    "premature_advice",
                    "discount_emotion",
                ],
            }
        ],
    }
    result = runner_mod._run_framework_adherence_real([conv])
    payload = stub_client.calls[0]["messages"][0]["content"]
    for prefixed in ("not:recommend_program", "not:premature_advice", "not:discount_emotion"):
        assert f'"name": "{prefixed}"' in payload
    assert result.detail["soft_criteria"]["not:recommend_program"] == {
        "passed": 1,
        "total": 1,
    }


# ── Verdict propagation ───────────────────────────────────────────────────


def test_judge_failure_fails_the_turn(monkeypatch: pytest.MonkeyPatch):
    """A single criterion FAIL must make the whole turn fail."""
    judge_scores = [
        [
            {"name": "acknowledge_emotion_specifically", "passed": False, "reason": "empty praise"},
            {"name": "ask_basic_layer_question", "passed": True, "reason": "x"},
        ]
    ]
    _patch_real_mode(monkeypatch, judge_scores=judge_scores)

    conv = {
        "id": "synth",
        "scripted_user_turns": ["hi"],
        "expectations": [
            {
                "turn_index": 0,
                "must_do": [
                    "acknowledge_emotion_specifically",
                    "ask_basic_layer_question",
                ],
            }
        ],
    }
    result = runner_mod._run_framework_adherence_real([conv])
    assert result.detail["passed_turns"] == 0
    assert result.detail["scored_turns"] == 1
    # The failing criterion is visible in the detail block.
    assert result.detail["soft_criteria"]["acknowledge_emotion_specifically"] == {
        "passed": 0,
        "total": 1,
    }
    assert result.detail["soft_criteria"]["ask_basic_layer_question"] == {
        "passed": 1,
        "total": 1,
    }


def test_judge_all_pass_with_no_structural_violation_passes_turn(
    monkeypatch: pytest.MonkeyPatch,
):
    judge_scores = [
        [
            {"name": "acknowledge_emotion_specifically", "passed": True, "reason": "x"},
            {"name": "redirect_to_discovery", "passed": True, "reason": "x"},
        ]
    ]
    _patch_real_mode(monkeypatch, judge_scores=judge_scores)

    conv = {
        "id": "synth",
        "scripted_user_turns": ["hi"],
        "expectations": [
            {
                "turn_index": 0,
                "must_do": ["acknowledge_emotion_specifically", "redirect_to_discovery"],
            }
        ],
    }
    result = runner_mod._run_framework_adherence_real([conv])
    assert result.passed, result.detail
    assert result.detail["passed_turns"] == 1


# ── Mode tag + detail shape ────────────────────────────────────────────────


def test_detail_block_marks_mode_as_real_plus_soft(
    monkeypatch: pytest.MonkeyPatch,
):
    """The mode tag tells admins whether the judge actually ran. Before
    this PR it said 'real-structural', misleading because the judge
    was already wired. Now it says 'real+soft' to make the layering
    explicit."""
    _patch_real_mode(monkeypatch, judge_scores=[[]])
    conv = {
        "id": "synth",
        "scripted_user_turns": ["hi"],
        "expectations": [
            {"turn_index": 0, "must_not_do": ["ask_more_than_one_question"]},
        ],
    }
    result = runner_mod._run_framework_adherence_real([conv])
    assert result.detail["mode"] == "real+soft"


def test_must_extract_criteria_routed_to_judge(monkeypatch: pytest.MonkeyPatch):
    """The structured extractor-shaped criteria still go through the
    judge alongside must_do entries."""
    judge_scores = [
        [
            {
                "name": "must_extract_identity_claim",
                "passed": True,
                "reason": "reflected value back",
            },
        ]
    ]
    stub_client, _ = _patch_real_mode(monkeypatch, judge_scores=judge_scores)
    conv = {
        "id": "synth",
        "scripted_user_turns": ["hi"],
        "expectations": [
            {
                "turn_index": 0,
                "must_extract_identity_claim": {
                    "facet": "value",
                    "evidence_must_quote": "help people",
                },
            }
        ],
    }
    runner_mod._run_framework_adherence_real([conv])
    payload = stub_client.calls[0]["messages"][0]["content"]
    assert "must_extract_identity_claim" in payload
    assert "help people" in payload  # spec carried through


def test_no_soft_criteria_skips_judge_call(monkeypatch: pytest.MonkeyPatch):
    """If a turn has only structural criteria, the judge is still
    consulted (it returns an empty scores list when there's nothing to
    grade) — but it doesn't crash and doesn't add criteria to the
    detail block."""
    stub_client, _ = _patch_real_mode(monkeypatch, judge_scores=[])

    conv = {
        "id": "synth",
        "scripted_user_turns": ["hi"],
        "expectations": [
            {"turn_index": 0, "must_not_do": ["ask_more_than_one_question"]},
        ],
    }
    result = runner_mod._run_framework_adherence_real([conv])
    # No soft criteria were extracted → judge wasn't called at all.
    assert stub_client.calls == []
    # Detail block still well-formed.
    assert result.detail["scored_turns"] == 1
    assert result.detail["soft_criteria"] == {}


# Keep the existing harness imports + monkeypatch path stable so the
# module is importable from the eval CLI without changes.
assert hasattr(evals_pkg, "__path__"), "evals package import broken"
asyncio  # avoid F401 — the module-level import documents the async surface
