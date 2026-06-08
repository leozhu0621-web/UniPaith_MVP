"""Uni counselor eval (Plan task 4) — deterministic, gates in CI without a key."""

from __future__ import annotations

from unipaith.ai.evals.uni_counselor import score_counselor_turn


def test_eval_flags_a_bad_turn() -> None:
    bad = "lol nice. what's your gpa? what's your major? where do you wanna go?"
    r = score_counselor_turn("I liked bio", bad)
    assert not r.passed
    assert "slang" in r.reasons
    assert "multiple_questions" in r.reasons


def test_eval_passes_a_counselor_turn() -> None:
    good = (
        "It sounds like bio really drew you in. When you were in it, what part "
        "made you lose track of time?"
    )
    r = score_counselor_turn("I liked bio", good)
    assert r.passed
    assert r.reasons == []


def test_eval_flags_no_reflection() -> None:
    # On-topic single question but no acknowledgement/echo of the student.
    r = score_counselor_turn("I love robotics", "Where do you want to apply?")
    assert not r.passed
    assert "no_reflection" in r.reasons


def test_eval_first_turn_needs_no_reflection() -> None:
    # No prior student turn (the opener) → reflection not required.
    r = score_counselor_turn("", "Welcome — when did you last feel really absorbed?")
    assert r.passed


def test_eval_flags_off_stage_turn() -> None:
    from unipaith.ai.evals.uni_counselor import score_stage_turn

    r = score_stage_turn(stage="goals", assistant="What's your favorite color?")
    assert not r.passed
    assert "off_stage" in r.reasons


def test_eval_passes_on_stage_turn() -> None:
    from unipaith.ai.evals.uni_counselor import score_stage_turn

    r = score_stage_turn(
        stage="goals",
        assistant="When you picture life after college — a career, a field, or still open?",
    )
    assert r.passed
    assert r.reasons == []
