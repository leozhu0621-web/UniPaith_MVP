"""Phase A3.2 — Validator track-level dispatch tests."""

from __future__ import annotations

import pytest

from unipaith.ai.client import AIClient
from unipaith.ai.state import (
    GoalEntry,
    NeedEntry,
    StudentSnapshot,
)
from unipaith.ai.validator import LayerValidator


def _mock_client() -> AIClient:
    return AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )


def test_validate_track_dispatches_goals() -> None:
    v = LayerValidator(client=_mock_client(), use_llm_judge=False)
    snap = StudentSnapshot(
        goals=[
            GoalEntry(
                category="academic",
                specific="MPH",
                measurable="m",
                achievable="a",
                relevant="r",
                time_bound="2027",
                completeness=1.0,
                user_confirmed=True,
            )
        ]
    )
    verdict = v.validate_track(track="goals", snapshot=snap)
    assert verdict.layer_complete is False  # only 1/3 categories
    assert "goals.social" in verdict.missing_signals


def test_validate_track_dispatches_needs() -> None:
    v = LayerValidator(client=_mock_client(), use_llm_judge=False)
    snap = StudentSnapshot(
        needs=[NeedEntry(maslow_level="safety", signal="visa_support")]
    )
    verdict = v.validate_track(track="needs", snapshot=snap)
    assert verdict.layer_complete is False
    assert "needs.physiological" in verdict.missing_signals


def test_validate_track_rejects_profile() -> None:
    """Profile is layered — must use validate(layer=...) for it."""
    v = LayerValidator(client=_mock_client(), use_llm_judge=False)
    with pytest.raises(ValueError, match="not flat"):
        v.validate_track(track="profile", snapshot=StudentSnapshot())  # type: ignore[arg-type]


def test_validate_track_rejects_unknown() -> None:
    v = LayerValidator(client=_mock_client(), use_llm_judge=False)
    with pytest.raises(ValueError):
        v.validate_track(track="bogus", snapshot=StudentSnapshot())  # type: ignore[arg-type]
