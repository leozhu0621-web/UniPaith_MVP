"""Spec 3 §3 — the three previously-unwired typed fit functions, now live in
the CPEF engine, plus per-dimension priors (§2.1). Pure-Python, no DB.

Before this change ``_build_cpef_signals`` only emitted themes/needs/budget/geo/
degree_level — ``fit_categorical`` (field-of-study related grading),
``fit_numeric_target`` (desired time-to-degree) and ``fit_boolean``
(flexibility / support wants) had boundary tests but were never assembled into
the score. These tests drive the REAL engine (``cpef`` / ``mutual_match``) and
assert the new signals appear and move the number, while staying gated so
absent data injects no phantom dimension.
"""

from unipaith.services.match.params import DEFAULT_PARAMS
from unipaith.services.matching import (
    ProgramFeatures,
    StudentFeatures,
    _build_cpef_signals,
    cpef,
    cpef_program_to_student,
    rank_programs,
)


def _sig_keys(student, program):
    signals, _db, _w = _build_cpef_signals(student, program, DEFAULT_PARAMS)
    return [s["key"] for s in signals]


# ── field-of-study categorical fit (s→p) ─────────────────────────────────────


def test_field_categorical_signal_emitted_when_both_sides_present():
    stu = StudentFeatures(sparse={"field_of_study": "data_science"})
    prog = ProgramFeatures(program_id="p", sparse={"fields_offered": ["data_science"]})
    assert "field" in _sig_keys(stu, prog)


def test_field_categorical_absent_when_student_field_unset():
    stu = StudentFeatures(sparse={})  # no field → no phantom signal
    prog = ProgramFeatures(program_id="p", sparse={"fields_offered": ["data_science"]})
    assert "field" not in _sig_keys(stu, prog)


def test_field_categorical_absent_when_program_offers_unknown():
    stu = StudentFeatures(sparse={"field_of_study": "data_science"})
    prog = ProgramFeatures(program_id="p", sparse={})  # no fields_offered
    assert "field" not in _sig_keys(stu, prog)


def test_field_exact_beats_related_beats_unrelated():
    prog_exact = ProgramFeatures(program_id="e", sparse={"fields_offered": ["data_science"]})
    prog_related = ProgramFeatures(program_id="r", sparse={"fields_offered": ["statistics"]})
    prog_unrelated = ProgramFeatures(program_id="u", sparse={"fields_offered": ["art_history"]})
    stu = StudentFeatures(sparse={"field_of_study": "data_science"}, extractor_quality=0.9)

    def field_f(prog):
        signals, _d, _w = _build_cpef_signals(stu, prog, DEFAULT_PARAMS)
        return next(s["f"] for s in signals if s["key"] == "field")

    assert field_f(prog_exact) == 1.0
    assert 0.0 < field_f(prog_related) < 1.0  # curated sim table grades it
    assert field_f(prog_unrelated) == 0.0


def test_field_uses_best_of_offered_list():
    # Program offers an unrelated AND the student's field → exact match wins.
    stu = StudentFeatures(sparse={"field_of_study": "data_science"})
    prog = ProgramFeatures(
        program_id="p", sparse={"fields_offered": ["art_history", "data_science"]}
    )
    signals, _d, _w = _build_cpef_signals(stu, prog, DEFAULT_PARAMS)
    assert next(s["f"] for s in signals if s["key"] == "field") == 1.0


# ── desired time-to-degree (numeric-target, s→p) ─────────────────────────────


def test_time_signal_emitted_only_when_student_states_a_target():
    prog = ProgramFeatures(program_id="p", sparse={"duration_months": 24})
    with_target = StudentFeatures(sparse={"desired_time_to_degree_months": 24})
    without = StudentFeatures(sparse={})
    assert "time" in _sig_keys(with_target, prog)
    assert "time" not in _sig_keys(without, prog)


def test_time_exact_match_scores_higher_than_far_off():
    stu = StudentFeatures(sparse={"desired_time_to_degree_months": 24}, extractor_quality=0.9)
    near = ProgramFeatures(program_id="n", sparse={"duration_months": 24})
    far = ProgramFeatures(program_id="f", sparse={"duration_months": 48})

    def time_f(prog):
        signals, _d, _w = _build_cpef_signals(stu, prog, DEFAULT_PARAMS)
        return next(s["f"] for s in signals if s["key"] == "time")

    assert time_f(near) == 1.0
    assert time_f(far) < time_f(near)


# ── flexibility / support boolean wants (s→p) ────────────────────────────────


def test_flexibility_signal_emitted_only_when_wanted():
    prog = ProgramFeatures(program_id="p", sparse={"part_time_available": True})
    wants = StudentFeatures(sparse={"wants_part_time": True})
    no_want = StudentFeatures(sparse={})
    assert "flexibility" in _sig_keys(wants, prog)
    assert "flexibility" not in _sig_keys(no_want, prog)


def test_flexibility_has_it_beats_lacks_it():
    stu = StudentFeatures(sparse={"wants_part_time": True}, extractor_quality=0.9)
    has = ProgramFeatures(program_id="h", sparse={"part_time_available": True})
    lacks = ProgramFeatures(program_id="l", sparse={"part_time_available": False})

    def flex_f(prog):
        signals, _d, _w = _build_cpef_signals(stu, prog, DEFAULT_PARAMS)
        return next(s["f"] for s in signals if s["key"] == "flexibility")

    assert flex_f(has) == 1.0
    assert flex_f(lacks) == 0.0


def test_online_want_also_drives_flexibility():
    stu = StudentFeatures(sparse={"wants_online": True})
    prog = ProgramFeatures(program_id="p", sparse={"online_available": True})
    assert "flexibility" in _sig_keys(stu, prog)


def test_support_want_emits_signal_and_grades():
    stu = StudentFeatures(sparse={"wants_career_support": True}, extractor_quality=0.9)
    has = ProgramFeatures(program_id="h", sparse={"career_services": True})
    lacks = ProgramFeatures(program_id="l", sparse={"career_services": False})
    assert "support" in _sig_keys(stu, has)

    def support_f(prog):
        signals, _d, _w = _build_cpef_signals(stu, prog, DEFAULT_PARAMS)
        return next(s["f"] for s in signals if s["key"] == "support")

    assert support_f(has) == 1.0
    assert support_f(lacks) < support_f(has)


def test_all_new_signals_compound_into_a_full_match():
    """A student wanting field+time+flexibility+support, met on every one, scores
    higher than the same student against a program meeting none of them."""
    stu = StudentFeatures(
        sparse={
            "field_of_study": "data_science",
            "desired_time_to_degree_months": 24,
            "wants_part_time": True,
            "wants_career_support": True,
            "interest_themes": ["data_science"],
        },
        extractor_quality=0.95,
    )
    perfect = ProgramFeatures(
        program_id="perfect",
        sparse={
            "fields_offered": ["data_science"],
            "duration_months": 24,
            "part_time_available": True,
            "career_services": True,
            "interest_themes": ["data_science"],
        },
        data_completeness=0.9,
    )
    poor = ProgramFeatures(
        program_id="poor",
        sparse={
            "fields_offered": ["art_history"],
            "duration_months": 60,
            "part_time_available": False,
            "career_services": False,
            "interest_themes": ["data_science"],
        },
        data_completeness=0.9,
    )
    m_perfect, _ = cpef(stu, perfect)
    m_poor, _ = cpef(stu, poor)
    assert m_perfect > m_poor
    assert 0.0 <= m_poor <= m_perfect <= 1.0


# ── p→s direction: field is graded, not exact-only ───────────────────────────


def test_p2s_related_field_no_longer_reads_as_hard_zero():
    """Spec 3 §3: the program→student field comparison must use the categorical
    sim table, so a related-field applicant is not a hard 0 to the program."""
    stu_related = StudentFeatures(sparse={"field_of_study": "statistics"})
    stu_unrelated = StudentFeatures(sparse={"field_of_study": "art_history"})
    prog = ProgramFeatures(
        program_id="p",
        sparse={"pref_fields": ["data_science"], "pref_min_gpa": 3.0},
        data_completeness=0.9,
    )
    related, _ = cpef_program_to_student(stu_related, prog)
    unrelated, _ = cpef_program_to_student(stu_unrelated, prog)
    assert related > unrelated  # statistics ≈ data_science scores above art_history


# ── per-dimension priors (§2.1 — not flat 0.5 everywhere) ────────────────────


def test_priors_are_not_all_flat_half():
    stu = StudentFeatures(
        sparse={
            "field_of_study": "data_science",
            "interest_themes": ["data_science"],
            "needs_signals": {"financial_aid": 0.8},
            "budget_max_usd_per_year": 40000,
            "geo_must": ["USA"],
        }
    )
    prog = ProgramFeatures(
        program_id="p",
        sparse={
            "fields_offered": ["data_science"],
            "interest_themes": ["data_science"],
            "tuition_usd_per_year": 30000,
            "locations": ["USA"],
        },
    )
    signals, _d, _w = _build_cpef_signals(stu, prog, DEFAULT_PARAMS)
    priors = {s["key"]: s["prior"] for s in signals}
    assert len(set(priors.values())) > 1, f"priors are flat: {priors}"
    # every prior stays a valid base rate in [0,1]
    assert all(0.0 <= v <= 1.0 for v in priors.values())


def test_thin_profile_shrinks_toward_per_dim_prior_not_global_half():
    """With a low-confidence (thin) profile, f̂ shrinks toward the signal's own
    prior. A dimension whose prior differs from 0.5 must land away from 0.5."""
    stu = StudentFeatures(
        sparse={"interest_themes": ["data_science"]},
        extractor_quality=0.05,  # very thin → rho≈0 → f̂≈prior
    )
    prog = ProgramFeatures(
        program_id="p",
        sparse={"interest_themes": ["data_science"]},
        data_completeness=0.99,
    )
    _v, bd = cpef(stu, prog)
    themes = next(s for s in bd["signals"] if s["key"] == "themes")
    # themes prior is intentionally below 0.5 (a random pair rarely shares tags),
    # so a thin profile's f̂ for themes sits below the old flat-0.5 anchor.
    assert themes["fhat"] < 0.5


# ── §4 tie-break: M, then coverage Σ A_k, then raw Σ f_k ──────────────────────


def test_cpef_breakdown_exposes_tiebreak_sums():
    stu = StudentFeatures(
        sparse={"interest_themes": ["data_science"], "geo_must": ["USA"]},
        extractor_quality=0.8,
    )
    prog = ProgramFeatures(
        program_id="p",
        sparse={"interest_themes": ["data_science"], "locations": ["USA"]},
        data_completeness=0.8,
    )
    _v, bd = cpef(stu, prog)
    assert "coverage_sum" in bd and "raw_fit_sum" in bd
    assert bd["coverage_sum"] > 0 and bd["raw_fit_sum"] > 0


def test_rank_tiebreak_uses_coverage_when_m_ties():
    """Two programs with (near-)equal M should order by coverage Σ A_k — the
    program backed by more present, confident signal ranks first (Spec 3 §4)."""
    stu = StudentFeatures(
        sparse={
            "interest_themes": ["data_science"],
            "budget_max_usd_per_year": 40000,
            "geo_must": ["USA"],
        },
        extractor_quality=0.85,
    )
    # Both match themes identically; "more_signals" additionally satisfies budget
    # + geo (more present coverage) at the SAME per-signal fit (1.0), so its M is
    # >= the themes-only program and its coverage_sum strictly greater.
    more_signals = ProgramFeatures(
        program_id="more_signals",
        sparse={
            "interest_themes": ["data_science"],
            "tuition_usd_per_year": 30000,
            "locations": ["USA"],
        },
        data_completeness=0.85,
    )
    themes_only = ProgramFeatures(
        program_id="themes_only",
        sparse={"interest_themes": ["data_science"]},
        data_completeness=0.85,
    )
    ranked = rank_programs(stu, [themes_only, more_signals], cpef_enabled=True)
    assert ranked[0][0].program_id == "more_signals"
