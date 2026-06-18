"""Spec 06 §3 / §5.5 / §7 — asymmetric match-rationale contract.

The invariant: the STUDENT projection of a match rationale never carries an
institution-only comparative/internal signal, while the INSTITUTION
projection is loss-less. These are pure-function tests on the single
source-of-truth redaction map, so they run without a DB or the LLM.
"""

from __future__ import annotations

from unipaith.ai.rationale_redaction import (
    INSTITUTION_ONLY_KEY_SUBSTRINGS,
    flatten_keys,
    is_institution_only,
    project_for_institution,
    project_for_student,
    redact_citations,
    redact_mapping,
    scrub_numbers_from_text,
)

# A representative rationale artifact: student-own signals + public program
# facts (safe) mixed with comparative/internal signals (institution-only).
CITED_STUDENT = ["sparse.research_experience", "sparse.gpa", "applicant_summary"]
CITED_PROGRAM = [
    "program.outcomes",  # public — safe
    "program.curriculum",  # public — safe
    "program.selectivity_delta",  # institution-only
    "program.cohort_percentile",  # institution-only
    "program.seat_capacity",  # institution-only
]
FITNESS_BREAKDOWN = {
    "academic_fit": 0.82,
    "goal_alignment": 0.74,
    "cohort_percentile": 0.91,  # institution-only
    "selectivity_pressure": 0.4,  # institution-only
}
CONFIDENCE_BREAKDOWN = {
    "reason": "high profile completeness",
    "profile_completeness": 0.8,
    "calibration": {"raw": 0.5, "calibrated": 0.55, "calibrator_n_samples": 1200},
    "peer_comparison": {"band": "top-quartile"},  # institution-only
}


def test_is_institution_only_matches_comparative_keys():
    assert is_institution_only("cohort_percentile")
    assert is_institution_only("selectivity_delta")
    assert is_institution_only("calibrator_n_samples")
    assert is_institution_only("seat_capacity")
    assert is_institution_only("peer_comparison")
    # student-own / public facts are NOT institution-only
    assert not is_institution_only("research_experience")
    assert not is_institution_only("academic_fit")
    assert not is_institution_only("outcomes")
    assert not is_institution_only("")


def test_redact_citations_drops_only_sensitive_paths():
    out = redact_citations(CITED_PROGRAM)
    assert "program.outcomes" in out
    assert "program.curriculum" in out
    assert "program.selectivity_delta" not in out
    assert "program.cohort_percentile" not in out
    assert "program.seat_capacity" not in out


def test_redact_mapping_is_recursive_and_nonmutating():
    src = dict(CONFIDENCE_BREAKDOWN)
    out = redact_mapping(src)
    # nested calibrator internals + peer comparison removed
    assert "calibration" not in out
    assert "peer_comparison" not in out
    assert out["reason"] == "high profile completeness"
    assert out["profile_completeness"] == 0.8
    # original untouched (institution projection of the same row stays intact)
    assert "calibration" in src
    assert "peer_comparison" in src


def test_student_projection_withholds_all_institution_only_signals():
    proj = project_for_student(
        rationale_text="Strong fit for your research goals.",
        cited_student_fields=CITED_STUDENT,
        cited_program_fields=CITED_PROGRAM,
        fitness_breakdown=FITNESS_BREAKDOWN,
        confidence_breakdown=CONFIDENCE_BREAKDOWN,
    )
    # The student keeps their own signals + public program facts.
    assert proj.cited_student_fields == CITED_STUDENT
    assert "program.outcomes" in proj.cited_program_fields
    # …but no comparative/internal program citations.
    assert "program.selectivity_delta" not in proj.cited_program_fields
    assert "program.cohort_percentile" not in proj.cited_program_fields
    # …and no institution-only breakdown key, at any depth.
    leaked = flatten_keys(proj.fitness_breakdown) | flatten_keys(proj.confidence_breakdown)
    for key in leaked:
        assert not is_institution_only(key), f"student projection leaked '{key}'"
    assert proj.redacted is True
    assert proj.audience == "student"


def test_institution_projection_is_lossless():
    proj = project_for_institution(
        rationale_text="Strong fit for your research goals.",
        cited_student_fields=CITED_STUDENT,
        cited_program_fields=CITED_PROGRAM,
        fitness_breakdown=FITNESS_BREAKDOWN,
        confidence_breakdown=CONFIDENCE_BREAKDOWN,
    )
    # Every comparative/internal signal is present for the reviewer.
    assert "program.selectivity_delta" in proj.cited_program_fields
    assert "program.cohort_percentile" in proj.cited_program_fields
    assert "cohort_percentile" in proj.fitness_breakdown
    assert "calibration" in proj.confidence_breakdown
    assert proj.confidence_breakdown["calibration"]["calibrator_n_samples"] == 1200
    assert proj.redacted is False
    assert proj.audience == "institution"


def test_student_and_institution_views_diverge_only_on_sensitive_signals():
    student = project_for_student(
        rationale_text="x",
        cited_student_fields=CITED_STUDENT,
        cited_program_fields=CITED_PROGRAM,
        fitness_breakdown=FITNESS_BREAKDOWN,
        confidence_breakdown=CONFIDENCE_BREAKDOWN,
    )
    institution = project_for_institution(
        rationale_text="x",
        cited_student_fields=CITED_STUDENT,
        cited_program_fields=CITED_PROGRAM,
        fitness_breakdown=FITNESS_BREAKDOWN,
        confidence_breakdown=CONFIDENCE_BREAKDOWN,
    )
    # Same prose + same student citations; difference is exactly the
    # institution-only program signals.
    assert student.rationale_text == institution.rationale_text
    assert student.cited_student_fields == institution.cited_student_fields
    only_in_institution = set(institution.cited_program_fields) - set(student.cited_program_fields)
    assert only_in_institution == {
        "program.selectivity_delta",
        "program.cohort_percentile",
        "program.seat_capacity",
    }


def test_redaction_map_is_nonempty():
    # Guardrail: an empty map would silently disable the asymmetry.
    assert len(INSTITUTION_ONLY_KEY_SUBSTRINGS) >= 10


# ── §14 string-channel scrubber ──────────────────────────────────────────────


def test_scrub_numbers_removes_every_digit():
    leaky = [
        "Fitness 0.85: drivers — gpa_alignment. Confidence 0.70: profile_complete.",
        "You are a 95% match with a 3.8 GPA.",
        "Top 10 percent; admit rate is 12.5%.",
    ]
    for text in leaky:
        out = scrub_numbers_from_text(text)
        assert not any(ch.isdigit() for ch in out), f"digit survived: {out!r}"


def test_scrub_numbers_preserves_clean_prose():
    clean = "Strong fit, driven by your research goals. Our confidence is high."
    assert scrub_numbers_from_text(clean) == clean


def test_scrub_numbers_handles_empty_and_none():
    assert scrub_numbers_from_text("") == ""
    assert scrub_numbers_from_text(None) == ""


def test_project_for_student_scrubs_numeric_rationale_text():
    # §14: even if the LLM/stub emits a number, the student projection strips it.
    proj = project_for_student(
        rationale_text="Fitness 0.82 makes this a 90% match.",
        cited_student_fields=[],
        cited_program_fields=[],
    )
    assert not any(ch.isdigit() for ch in proj.rationale_text)
