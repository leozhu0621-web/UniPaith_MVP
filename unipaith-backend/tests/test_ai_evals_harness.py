"""Phase A1 — smoke tests for the AI eval harness.

Verifies the harness loads fixtures, returns SuiteResults with expected
shape, and the mock-mode runner exits 0 when fixtures are well-formed.
This is what gates the harness itself; the agents land in A2+.
"""

from __future__ import annotations

import json

from unipaith.ai.evals.runner import (
    SUITES,
    THRESHOLDS,
    SuiteResult,
    load_extractor_units,
    load_golden_conversations,
    main,
    run_extractor_accuracy,
    run_framework_adherence,
)


def test_thresholds_present_for_every_suite() -> None:
    for suite in SUITES:
        assert suite in THRESHOLDS, f"{suite} missing threshold definition"


def test_load_golden_conversations_finds_first_gen_engineer() -> None:
    convs = load_golden_conversations()
    assert len(convs) >= 1
    ids = {c.get("id") for c in convs}
    assert "first_gen_engineer" in ids


def test_load_extractor_units_parses_jsonl_with_comments() -> None:
    units = load_extractor_units()
    # Phase A2 grew the labeled set from 5 to 20.
    assert len(units) >= 20
    # Comment lines starting with `// ` must be stripped, not parsed.
    for u in units:
        assert isinstance(u, dict)
        assert "id" in u
        assert "student_turn" in u
        assert "expected" in u


def test_extractor_unit_ids_unique() -> None:
    """Stable IDs are how we track regressions across runs — must be unique."""
    units = load_extractor_units()
    ids = [u["id"] for u in units]
    assert len(ids) == len(set(ids))


def test_framework_adherence_mock_mode_passes() -> None:
    result = run_framework_adherence(real=False)
    assert isinstance(result, SuiteResult)
    assert result.name == "framework_adherence"
    assert result.passed, f"Mock-mode framework_adherence failed: {result.detail}"


def test_extractor_accuracy_mock_mode_passes() -> None:
    result = run_extractor_accuracy(real=False)
    assert result.passed, f"Mock-mode extractor_accuracy failed: {result.detail}"


def test_main_all_suites_mock_mode_returns_zero() -> None:
    """The full eval harness in mock mode must exit 0 on Phase A1 fixtures."""
    rc = main(["--suite", "all"])
    assert rc == 0, "Eval harness regressed — check fixture files"


def test_golden_conversation_has_required_structure() -> None:
    convs = load_golden_conversations()
    fge = next(c for c in convs if c.get("id") == "first_gen_engineer")
    # Validate the shape every fixture must have.
    assert "persona" in fge
    assert "scripted_user_turns" in fge
    assert "expectations" in fge
    assert len(fge["scripted_user_turns"]) >= 5
    # First turn must check the redirect-from-recommendation rule.
    first_exp = fge["expectations"][0]
    assert "must_not_do" in first_exp
    assert any(
        "recommend" in m for m in first_exp["must_not_do"]
    ), "First turn must guard against premature program recommendations"


def test_extractor_units_have_evidence_for_identity_claims() -> None:
    """Every identity claim in the labeled set must include an evidence field."""
    units = load_extractor_units()
    for u in units:
        identity = u.get("expected", {}).get("identity", [])
        for claim in identity:
            assert "evidence" in claim, (
                f"Unit {u.get('id')}: identity claim missing evidence — "
                "this would defeat the depth-ladder framework."
            )


def test_extractor_units_jsonl_lines_are_valid_json() -> None:
    """Make sure no fixture line is silently malformed."""
    from pathlib import Path

    p = (
        Path(__file__).parents[1]
        / "src"
        / "unipaith"
        / "ai"
        / "evals"
        / "fixtures"
        / "extractor_units.jsonl"
    )
    assert p.exists()
    with p.open() as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                raise AssertionError(
                    f"Line {line_no} of extractor_units.jsonl is invalid JSON: {e}"
                )
