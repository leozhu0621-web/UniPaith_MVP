"""Phase A2 — Layer Validator tests.

A2 ships only the BASIC pathway (deterministic). PERSONALITY/IDENTITY raise
NotImplementedError until A3.
"""

from __future__ import annotations

import pytest

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


def test_validate_personality_raises_not_implemented() -> None:
    """A2 doesn't ship personality validation — it lands in A3."""
    with pytest.raises(NotImplementedError, match="A2 ships BASIC only"):
        default_validator.validate(layer="personality", snapshot=StudentSnapshot())


def test_validate_identity_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="A2 ships BASIC only"):
        default_validator.validate(layer="identity", snapshot=StudentSnapshot())
