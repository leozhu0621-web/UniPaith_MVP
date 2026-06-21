"""Slice B — two-sided CPEF: p→s direction + mutual-fit blend M (Spec 3 §4). Pure, no DB."""

from unipaith.services.match.params import DEFAULT_PARAMS
from unipaith.services.matching import (
    ProgramFeatures,
    StudentFeatures,
    cpef,
    cpef_program_to_student,
    mutual_match,
    score,
)


def _student():
    return StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "budget_max_usd_per_year": 35000,
            "interest_themes": ["data_science"],
            "gpa": 3.0,
            "field_of_study": "data_science",
        },
        profile_completeness=0.8,
    )


_GOOD = ProgramFeatures(
    program_id="good",
    sparse={
        "target_education_level": "masters",
        "locations": ["USA"],
        "tuition_usd_per_year": 30000,
        "interest_themes": ["data_science"],
    },
)


def test_no_program_prefs_means_no_opinion():
    ps, bd = cpef_program_to_student(_student(), _GOOD)
    assert ps == 1.0
    assert bd.get("no_prefs") is True


def test_program_disliking_student_pulls_m_down():
    s = _student()
    picky = ProgramFeatures(program_id="picky", sparse={**_GOOD.sparse, "pref_min_gpa": 3.9})
    m_base = float(score(s, _GOOD, cpef_enabled=True).fitness)
    m_picky = float(score(s, picky, cpef_enabled=True).fitness)
    assert m_picky < m_base


def test_well_matched_prefs_do_not_penalize():
    s = _student()
    wants = ProgramFeatures(
        program_id="wants",
        sparse={**_GOOD.sparse, "pref_fields": ["data_science"], "pref_levels": ["bachelors"]},
    )
    m_base = float(score(s, _GOOD, cpef_enabled=True).fitness)
    m_wants = float(score(s, wants, cpef_enabled=True).fitness)
    # student perfectly meets the program's preferences → p→s == 1.0 → M == base
    assert m_wants >= m_base - 1e-6


def test_alpha_one_reduces_to_one_directional():
    s = _student()
    picky = ProgramFeatures(program_id="picky", sparse={**_GOOD.sparse, "pref_min_gpa": 3.9})
    params = {**DEFAULT_PARAMS, "alpha": 1.0}
    m, _ = mutual_match(s, picky, params=params)
    sp, _ = cpef(s, picky, params=params)
    assert abs(m - sp) < 1e-9  # alpha=1 → M == CPEF_{s→p}


def test_mutual_breakdown_has_both_directions():
    m, bd = mutual_match(_student(), _GOOD)
    assert "p2s" in bd and "m" in bd and "alpha" in bd
    assert bd["model"] == "cpef"  # inherited from the s→p breakdown


# ── p→s grading correctness (audit batch B) ──────────────────────────────────


def test_gpa_at_floor_scores_high_not_neutral():
    # pref_min_gpa is an admit FLOOR — a student exactly AT it should read as a
    # strong fit (~0.85), not the cohort-mean 0.5 the old higher-is-better form
    # gave (which buried qualified applicants in the program's own direction).
    student = StudentFeatures(sparse={"gpa": 3.5})
    program = ProgramFeatures(program_id="floor", sparse={"pref_min_gpa": 3.5})
    _, bd = cpef_program_to_student(student, program)
    assert bd["satisfaction"] >= 0.8


def test_gpa_well_below_floor_still_scores_low():
    student = StudentFeatures(sparse={"gpa": 3.0})
    program = ProgramFeatures(program_id="floor", sparse={"pref_min_gpa": 3.8})
    _, bd = cpef_program_to_student(student, program)
    assert bd["satisfaction"] < 0.3


def test_career_arcs_graded_by_program_pref_coverage():
    # Program asks "how many of the arcs we prefer does this applicant carry"
    # → graded coverage, not the old binary any-overlap=1.0.
    prog = ProgramFeatures(program_id="careers", sparse={"pref_career_arcs": ["a", "b", "c", "d"]})

    def _sat(arcs: list[str]) -> float:
        _, bd = cpef_program_to_student(StudentFeatures(sparse={"career_arcs": arcs}), prog)
        return bd["satisfaction"]

    full = {"satisfaction": _sat(["a", "b", "c", "d"])}
    half = {"satisfaction": _sat(["a", "b"])}
    none = {"satisfaction": _sat(["x", "y"])}
    assert full["satisfaction"] == 1.0
    assert none["satisfaction"] == 0.0
    assert 0.4 < half["satisfaction"] < 0.6  # graded — old binary gave 1.0


def test_values_graded_by_program_pref_coverage():
    prog = ProgramFeatures(
        program_id="vals",
        sparse={"pref_values": ["impact", "rigor", "service", "curiosity"]},
    )
    half = cpef_program_to_student(StudentFeatures(sparse={"values": ["impact", "rigor"]}), prog)[1]
    assert 0.4 < half["satisfaction"] < 0.6
