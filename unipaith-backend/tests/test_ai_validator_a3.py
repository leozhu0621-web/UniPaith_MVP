"""Phase A3 — Validator tests for PERSONALITY + IDENTITY pathways.

Mock-mode: deterministic gate dispatch + judge fallback behavior.
"""

from __future__ import annotations

import asyncio

from unipaith.ai.client import AIClient
from unipaith.ai.state import PersonalityEntry, StudentSnapshot
from unipaith.ai.validator import (
    IDENTITY_JUDGE_THRESHOLD,
    PERSONALITY_JUDGE_THRESHOLD,
    JudgeOutcome,
    LayerValidator,
    _judge_followup_probe,
)


def _mock_client() -> AIClient:
    return AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )


# ── Sync dispatch ──────────────────────────────────────────────────────────


def test_validate_dispatches_personality_to_evaluator() -> None:
    v = LayerValidator(client=_mock_client(), use_llm_judge=False)
    snap = StudentSnapshot()
    verdict = v.validate(layer="personality", snapshot=snap)
    assert verdict.layer_complete is False
    assert verdict.completion_pct == 0


def test_validate_dispatches_identity_to_evaluator() -> None:
    v = LayerValidator(client=_mock_client(), use_llm_judge=False)
    verdict = v.validate(layer="identity", snapshot=StudentSnapshot())
    assert verdict.layer_complete is False
    # Three independent gates all missing.
    assert len(verdict.missing_signals) == 3


def test_validate_unknown_layer_raises() -> None:
    import pytest

    v = LayerValidator(client=_mock_client())
    with pytest.raises(ValueError, match="unknown layer"):
        v.validate(layer="bogus", snapshot=StudentSnapshot())  # type: ignore[arg-type]


# ── Async judge dispatch ───────────────────────────────────────────────────


def test_validate_with_judge_basic_returns_no_judge() -> None:
    v = LayerValidator(client=_mock_client())
    verdict, outcome = asyncio.run(v.validate_with_judge(layer="basic", snapshot=StudentSnapshot()))
    assert verdict.layer_complete is False
    assert outcome is None


def test_validate_with_judge_skips_when_deterministic_incomplete() -> None:
    """No tokens burned when count gate already says incomplete."""
    v = LayerValidator(client=_mock_client(), use_llm_judge=True)
    snap = StudentSnapshot(
        personality=[
            PersonalityEntry(facet="interest", value="ml", evidence="ev"),
        ]
    )
    verdict, outcome = asyncio.run(v.validate_with_judge(layer="personality", snapshot=snap))
    assert verdict.layer_complete is False
    assert outcome is None  # judge skipped


def test_validate_with_judge_disabled_returns_deterministic_only() -> None:
    v = LayerValidator(client=_mock_client(), use_llm_judge=False)
    snap = StudentSnapshot(
        personality=[
            PersonalityEntry(facet="interest", value="ml", evidence="ev1"),
            PersonalityEntry(facet="peer_style", value="small", evidence="ev2"),
            PersonalityEntry(facet="passion", value="teaching", evidence="ev3"),
            PersonalityEntry(facet="connection_style", value="mentor", evidence="ev4"),
        ]
    )
    verdict, outcome = asyncio.run(v.validate_with_judge(layer="personality", snapshot=snap))
    assert verdict.layer_complete is True
    assert outcome is None


def test_validate_with_judge_in_mock_mode_returns_failed_outcome() -> None:
    """Mock client returns text-only canned response (no tool_use); the
    validator's parse-judge path returns no scores → judge fails closed."""
    v = LayerValidator(client=_mock_client(), use_llm_judge=True)
    snap = StudentSnapshot(
        personality=[
            PersonalityEntry(facet="interest", value="ml", evidence="ev1"),
            PersonalityEntry(facet="peer_style", value="small", evidence="ev2"),
            PersonalityEntry(facet="passion", value="teaching", evidence="ev3"),
            PersonalityEntry(facet="connection_style", value="mentor", evidence="ev4"),
        ]
    )
    verdict, outcome = asyncio.run(v.validate_with_judge(layer="personality", snapshot=snap))
    # Deterministic gate passes, judge fails closed (mock returns no scores)
    # → gated layer_complete is False.
    assert outcome is not None
    assert outcome.passed is False
    assert verdict.layer_complete is False


# ── Judge response parsing ─────────────────────────────────────────────────


def test_parse_judge_response_extracts_scores() -> None:
    blocks = [
        {
            "type": "tool_use",
            "name": "score_identity_claims",
            "input": {
                "scores": [
                    {"facet": "value", "score": 4, "reason": "ok"},
                    {"facet": "belief", "score": 3, "reason": "ok"},
                ]
            },
        }
    ]
    scores = LayerValidator._parse_judge_response(blocks)
    assert len(scores) == 2
    assert scores[0]["score"] == 4


def test_parse_judge_response_filters_out_of_range() -> None:
    blocks = [
        {
            "type": "tool_use",
            "name": "score_identity_claims",
            "input": {
                "scores": [
                    {"facet": "value", "score": 4, "reason": "ok"},
                    {"facet": "belief", "score": 7, "reason": "out of range"},
                    {"facet": "view", "score": "five", "reason": "wrong type"},
                ]
            },
        }
    ]
    scores = LayerValidator._parse_judge_response(blocks)
    assert len(scores) == 1
    assert scores[0]["score"] == 4


def test_parse_judge_response_no_tool_use_returns_empty() -> None:
    blocks = [{"type": "text", "text": "no tool call"}]
    assert LayerValidator._parse_judge_response(blocks) == []


# ── Helpers + thresholds ───────────────────────────────────────────────────


def test_judge_followup_probe_returns_layer_specific() -> None:
    p = _judge_followup_probe("personality")
    assert "concrete" in p.lower()
    i = _judge_followup_probe("identity")
    assert "story" in i.lower()


def test_thresholds_are_calibrated_separately() -> None:
    """Identity is the deepest layer — its threshold should be stricter
    than personality. Document via test."""
    assert IDENTITY_JUDGE_THRESHOLD > PERSONALITY_JUDGE_THRESHOLD


def test_judge_outcome_dataclass_defaults() -> None:
    """Default JudgeOutcome (no entries provided) fails closed."""
    o = JudgeOutcome(mean_score=0.0, threshold=3.0, passed=False)
    assert o.passed is False
    assert o.per_entry == []
