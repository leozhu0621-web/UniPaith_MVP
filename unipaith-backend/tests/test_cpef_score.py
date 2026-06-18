"""Slice A — CPEF top-level score + flag branch (Spec 3). Pure, no DB."""

from unipaith.services.matching import ProgramFeatures, StudentFeatures, rank_programs, score

_STUDENT = StudentFeatures(
    sparse={
        "education_level": "bachelors",
        "geo_must": ["USA"],
        "budget_max_usd_per_year": 35000,
        "interest_themes": ["data_science"],
    },
    embedding=None,
    profile_completeness=0.8,
)

# Good: masters in USA, affordable, theme match.
_GOOD = ProgramFeatures(
    program_id="good",
    sparse={
        "target_education_level": "masters",
        "locations": ["USA"],
        "tuition_usd_per_year": 30000,
        "interest_themes": ["data_science"],
    },
)
# Pricey: mildly over budget (40k vs 35k = 14%, within tolerance → graded, not buried).
_PRICEY = ProgramFeatures(
    program_id="pricey",
    sparse={
        "target_education_level": "masters",
        "locations": ["USA"],
        "tuition_usd_per_year": 40000,
        "interest_themes": ["data_science"],
    },
)
# Degree-incompatible: a bachelors program for a bachelors-holder → confirmed deal-breaker.
_BAD = ProgramFeatures(
    program_id="bad",
    sparse={
        "target_education_level": "bachelors",
        "locations": ["USA"],
        "tuition_usd_per_year": 30000,
    },
)


def test_cpef_never_eliminates():
    assert score(_STUDENT, _BAD, cpef_enabled=True).eliminated is False


def test_cpef_ordering_good_beats_pricey_beats_dealbreaker():
    g = float(score(_STUDENT, _GOOD, cpef_enabled=True).fitness)
    p = float(score(_STUDENT, _PRICEY, cpef_enabled=True).fitness)
    b = float(score(_STUDENT, _BAD, cpef_enabled=True).fitness)
    assert g > p > b


def test_cpef_confirmed_dealbreaker_is_buried():
    b = float(score(_STUDENT, _BAD, cpef_enabled=True).fitness)
    assert b < 0.05  # hardened floor sinks it below every clean program


def test_flag_off_uses_legacy_hard_filter():
    # Legacy path eliminates the degree-incompatible program.
    assert score(_STUDENT, _BAD, cpef_enabled=False).eliminated is True


def test_coverage_fuller_profile_scores_higher():
    # A program matching on more present dimensions outranks a themes-only match.
    thin = ProgramFeatures(program_id="thin", sparse={"interest_themes": ["data_science"]})
    full_val = float(score(_STUDENT, _GOOD, cpef_enabled=True).fitness)
    thin_val = float(score(_STUDENT, thin, cpef_enabled=True).fitness)
    assert full_val > thin_val


def test_cpef_breakdown_is_explainable():
    s = score(_STUDENT, _GOOD, cpef_enabled=True)
    bd = s.fitness_breakdown
    assert bd["model"] == "cpef"
    assert {"value", "inner", "coverage", "veto", "signals", "dealbreakers"} <= bd.keys()
    # ranking must never appear as a scored signal
    assert all(sig["key"] != "ranking" for sig in bd["signals"])


def test_rank_programs_cpef_sorts_buried_last():
    ranked = rank_programs(
        _STUDENT, [_BAD, _GOOD, _PRICEY], cpef_enabled=True, include_eliminated=True
    )
    order = [p.program_id for p, _ in ranked]
    assert order[0] == "good"
    assert order[-1] == "bad"
