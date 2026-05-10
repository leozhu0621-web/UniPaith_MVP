"""Layer Validator tests — BASIC layer (Phase A2).

PERSONALITY + IDENTITY tests live in `test_ai_validator_a3.py` since they
require the A3 evaluators + LLM-as-judge plumbing.
"""

from __future__ import annotations

from unipaith.ai.state import StudentSnapshot
from unipaith.ai.validator import LayerValidator, default_validator


def test_default_validator_is_a_layer_validator() -> None:
    assert isinstance(default_validator, LayerValidator)


def test_validate_basic_delegates_to_state_evaluator() -> None:
    """The validator just dispatches to `evaluate_basic_layer` for BASIC."""
    snap = StudentSnapshot(
        age=20,
        education_level="bachelors",
        gpa=3.7,
        location_prefs=["US-NY"],
        first_gen=True,
    )
    v = default_validator.validate(layer="basic", snapshot=snap)
    assert v.layer_complete is True


def test_validate_basic_incomplete_returns_missing() -> None:
    v = default_validator.validate(layer="basic", snapshot=StudentSnapshot())
    assert v.layer_complete is False
    assert v.next_probe_hint is not None
