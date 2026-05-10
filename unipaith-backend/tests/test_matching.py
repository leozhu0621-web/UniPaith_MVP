"""Phase B1 — ML matcher unit tests.

Pure-Python; no DB or LLM. Covers hard filters, component scorers,
fitness composition, confidence math, ranking, and edge cases.
"""

from __future__ import annotations

from decimal import Decimal

from unipaith.services.matching import (
    DEFAULT_WEIGHTS,
    ProgramFeatures,
    StudentFeatures,
    cosine,
    needs_match,
    rank_programs,
    rule_pass,
    score,
    soft_align,
)

# ── DEFAULT_WEIGHTS sanity ─────────────────────────────────────────────────


def test_default_weights_sum_to_one() -> None:
    """Weights are interpretable as a convex combination — must sum to 1."""
    assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9


def test_default_weights_non_negative() -> None:
    for k, v in DEFAULT_WEIGHTS.items():
        assert v >= 0, f"weight {k}={v} is negative"


# ── Hard-filter rule layer ─────────────────────────────────────────────────


def test_rule_pass_education_compat_bachelors_to_masters() -> None:
    student = StudentFeatures(sparse={"education_level": "bachelors"})
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters"},
    )
    passed, _ = rule_pass(student, program)
    assert passed is True


def test_rule_pass_education_mismatch_high_school_to_masters() -> None:
    student = StudentFeatures(sparse={"education_level": "high_school"})
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters"},
    )
    passed, reason = rule_pass(student, program)
    assert passed is False
    assert "education_mismatch" in reason


def test_rule_pass_geo_must_intersection_required() -> None:
    student = StudentFeatures(
        sparse={"education_level": "bachelors", "geo_must": ["US-NY", "US-MA"]}
    )
    # Program in US-CA → no intersection → eliminated.
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters", "locations": ["US-CA"]},
    )
    passed, reason = rule_pass(student, program)
    assert passed is False
    assert "geo_must_disjoint" in reason


def test_rule_pass_geo_avoid_eliminates_when_program_only_there() -> None:
    student = StudentFeatures(
        sparse={"education_level": "bachelors", "geo_avoid": ["US-CA"]}
    )
    # All program locations are on the avoid list.
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters", "locations": ["US-CA"]},
    )
    passed, reason = rule_pass(student, program)
    assert passed is False
    assert "geo_avoid" in reason


def test_rule_pass_geo_avoid_passes_when_program_has_other_locations() -> None:
    """Avoid only filters when ALL program locations are avoided."""
    student = StudentFeatures(
        sparse={"education_level": "bachelors", "geo_avoid": ["US-CA"]}
    )
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters", "locations": ["US-CA", "US-NY"]},
    )
    passed, _ = rule_pass(student, program)
    assert passed is True


def test_rule_pass_budget_eliminates_when_no_aid() -> None:
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "budget_max_usd_per_year": 30000,
            "needs_aid": False,
        }
    )
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters", "tuition_usd_per_year": 60000},
    )
    passed, reason = rule_pass(student, program)
    assert passed is False
    assert "budget" in reason


def test_rule_pass_budget_skipped_when_aid_requested() -> None:
    """Students requesting aid don't get filtered on tuition — financial-
    aid programs may bridge the gap."""
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "budget_max_usd_per_year": 30000,
            "needs_aid": True,
        }
    )
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters", "tuition_usd_per_year": 60000},
    )
    passed, _ = rule_pass(student, program)
    assert passed is True


def test_rule_pass_no_program_target_means_open() -> None:
    student = StudentFeatures(sparse={"education_level": "high_school"})
    program = ProgramFeatures(program_id="p1", sparse={})  # no target_education_level
    passed, _ = rule_pass(student, program)
    assert passed is True


# ── Cosine ─────────────────────────────────────────────────────────────────


def test_cosine_identical_vectors_returns_one() -> None:
    v = [1.0, 0.5, 0.0, -0.3]
    assert abs(cosine(v, v) - 1.0) < 1e-9


def test_cosine_orthogonal_returns_zero() -> None:
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_clamps_negative_to_zero() -> None:
    """Per module docstring: free-text-summary cosine is clamped to [0,1]."""
    assert cosine([1.0, 0.0], [-1.0, 0.0]) == 0.0


def test_cosine_empty_or_mismatched_returns_zero() -> None:
    assert cosine(None, None) == 0.0
    assert cosine([1.0], None) == 0.0
    assert cosine([1.0, 2.0], [1.0]) == 0.0


def test_cosine_zero_vector_returns_zero() -> None:
    """Zero-norm vectors don't crash; return 0."""
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0


# ── Soft alignment ─────────────────────────────────────────────────────────


def test_soft_align_perfect_overlap() -> None:
    s = StudentFeatures(
        sparse={
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": ["intellectual_rigor"],
            "social_prefs": {"small_cohort": 0.9},
        }
    )
    p = ProgramFeatures(
        program_id="p1",
        sparse={
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": ["intellectual_rigor"],
            "social_features": {"small_cohort": 0.9},
        },
    )
    assert soft_align(s, p) > 0.9


def test_soft_align_zero_overlap_returns_zero() -> None:
    s = StudentFeatures(
        sparse={
            "interest_themes": ["philosophy"],
            "career_arcs": ["public_health_policy"],
            "values": [],
            "social_prefs": {},
        }
    )
    p = ProgramFeatures(
        program_id="p1",
        sparse={
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": [],
            "social_features": {},
        },
    )
    assert soft_align(s, p) == 0.0


def test_soft_align_partial_overlap() -> None:
    s = StudentFeatures(
        sparse={
            "interest_themes": ["machine_learning", "philosophy"],
            "career_arcs": ["ml_research"],
            "values": [],
            "social_prefs": {},
        }
    )
    p = ProgramFeatures(
        program_id="p1",
        sparse={
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": [],
            "social_features": {},
        },
    )
    s_score = soft_align(s, p)
    # 0.7 * (0.4 * 0.5 [interest jaccard] + 0.4 * 1.0 [career jaccard] + 0)
    # ≈ 0.7 * 0.6 = 0.42, plus 0 from social
    assert 0.3 < s_score < 0.5


# ── Needs match ────────────────────────────────────────────────────────────


def test_needs_match_full_coverage() -> None:
    s = StudentFeatures(
        sparse={"needs_signals": {"low_income_aid": 1.0, "near_family": 0.8}}
    )
    p = ProgramFeatures(
        program_id="p1",
        sparse={"support_signals": {"low_income_aid": 1.0, "near_family": 1.0}},
    )
    assert needs_match(s, p) > 0.9


def test_needs_match_zero_when_no_program_support() -> None:
    s = StudentFeatures(
        sparse={"needs_signals": {"low_income_aid": 1.0}}
    )
    p = ProgramFeatures(program_id="p1", sparse={"support_signals": {}})
    assert needs_match(s, p) == 0.0


def test_needs_match_neutral_when_student_has_no_needs() -> None:
    """No expressed needs → don't punish the program (return 0.5)."""
    s = StudentFeatures(sparse={"needs_signals": {}})
    p = ProgramFeatures(
        program_id="p1", sparse={"support_signals": {"alumni_network": 1.0}}
    )
    assert needs_match(s, p) == 0.5


def test_needs_match_severity_weighted() -> None:
    """Higher-severity needs count more."""
    s = StudentFeatures(
        sparse={
            "needs_signals": {
                "low_income_aid": 1.0,  # critical
                "alumni_network": 0.2,  # nice-to-have
            }
        }
    )
    # Program covers ONLY the high-severity need → still scores well.
    p_critical = ProgramFeatures(
        program_id="p1", sparse={"support_signals": {"low_income_aid": 1.0}}
    )
    # Program covers ONLY the low-severity need → should score lower.
    p_minor = ProgramFeatures(
        program_id="p2", sparse={"support_signals": {"alumni_network": 1.0}}
    )
    assert needs_match(s, p_critical) > needs_match(s, p_minor)


# ── Top-level scoring ──────────────────────────────────────────────────────


def test_score_eliminated_returns_zero_fitness() -> None:
    student = StudentFeatures(sparse={"education_level": "high_school"})
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "doctoral"},
    )
    s = score(student, program)
    assert s.eliminated is True
    assert s.fitness == Decimal("0.0000")
    assert s.confidence == Decimal("1.0000")
    assert s.fitness_breakdown.get("eliminated") is True


def test_score_breakdown_includes_components_and_weights() -> None:
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": [],
            "social_prefs": {},
            "needs_signals": {},
        },
        embedding=[0.1] * 1024,
        profile_completeness=0.8,
    )
    program = ProgramFeatures(
        program_id="p1",
        sparse={
            "target_education_level": "masters",
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": [],
            "social_features": {},
            "support_signals": {},
        },
        embedding=[0.1] * 1024,
        data_completeness=0.7,
    )
    s = score(student, program)
    assert not s.eliminated
    bd = s.fitness_breakdown
    assert "cosine" in bd
    assert "soft_align" in bd
    assert "needs_match" in bd
    assert bd["weights"] == DEFAULT_WEIGHTS


def test_confidence_geometric_mean_penalizes_low_term() -> None:
    """A low program_data_quality should drag confidence down even with
    a fully-known student."""
    student = StudentFeatures(
        sparse={"education_level": "bachelors"},
        profile_completeness=1.0,
        extractor_quality=1.0,
    )
    p_known = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters"},
        data_completeness=1.0,
    )
    p_unknown = ProgramFeatures(
        program_id="p2",
        sparse={"target_education_level": "masters"},
        data_completeness=0.2,
    )
    s_known = score(student, p_known)
    s_unknown = score(student, p_unknown)
    assert s_known.confidence > s_unknown.confidence
    # Geometric mean of (1, 1, 0.2, 1) = 0.2^0.25 ≈ 0.6687
    assert abs(float(s_unknown.confidence) - 0.6687) < 0.01


def test_confidence_zero_completeness_returns_zero_confidence() -> None:
    """If we don't know the student at all, confidence collapses."""
    student = StudentFeatures(
        sparse={"education_level": "unknown"}, profile_completeness=0.0
    )
    program = ProgramFeatures(program_id="p1", sparse={"target_education_level": None})
    s = score(student, program)
    assert s.confidence == Decimal("0.0000")


def test_score_fitness_in_unit_interval() -> None:
    """Fitness must always be in [0, 1] regardless of inputs."""
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "interest_themes": ["x"],
            "career_arcs": ["y"],
            "values": [],
            "social_prefs": {},
            "needs_signals": {},
        }
    )
    program = ProgramFeatures(
        program_id="p1",
        sparse={"target_education_level": "masters"},
    )
    s = score(student, program)
    assert Decimal("0") <= s.fitness <= Decimal("1")
    assert Decimal("0") <= s.confidence <= Decimal("1")


# ── Ranking ────────────────────────────────────────────────────────────────


def test_rank_programs_returns_sorted_desc() -> None:
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": [],
            "social_prefs": {},
            "needs_signals": {},
        },
        profile_completeness=0.8,
    )
    p_high = ProgramFeatures(
        program_id="p_high",
        sparse={
            "target_education_level": "masters",
            "interest_themes": ["machine_learning"],
            "career_arcs": ["ml_research"],
            "values": [],
            "social_features": {},
            "support_signals": {},
        },
    )
    p_low = ProgramFeatures(
        program_id="p_low",
        sparse={
            "target_education_level": "masters",
            "interest_themes": ["philosophy"],
            "career_arcs": ["academic_humanities"],
            "values": [],
            "social_features": {},
            "support_signals": {},
        },
    )
    # bachelors → doctoral IS valid (per education_compat table); we
    # use a geo mismatch instead to force elimination.
    p_geo = ProgramFeatures(
        program_id="p_geo",
        sparse={"target_education_level": "masters", "locations": ["MARS"]},
    )
    student_with_geo = StudentFeatures(
        sparse={**student.sparse, "geo_must": ["US-NY"]},
        profile_completeness=0.8,
    )
    ranked = rank_programs(student_with_geo, [p_geo, p_high, p_low])
    # p_geo should be eliminated and excluded by default.
    ids = [p.program_id for p, _ in ranked]
    assert "p_geo" not in ids
    # p_high before p_low
    assert ids[0] == "p_high"
    assert ids[1] == "p_low"


def test_rank_programs_with_include_eliminated_keeps_them_at_bottom() -> None:
    student = StudentFeatures(
        sparse={"education_level": "high_school", "geo_must": ["US-NY"]},
        profile_completeness=0.5,
    )
    p_elim = ProgramFeatures(
        program_id="p_elim",
        sparse={"target_education_level": "doctoral"},
    )
    p_ok = ProgramFeatures(
        program_id="p_ok",
        sparse={
            "target_education_level": "bachelors",
            "locations": ["US-NY"],
            "interest_themes": [],
            "career_arcs": [],
            "values": [],
            "social_features": {},
            "support_signals": {},
        },
    )
    ranked = rank_programs(student, [p_elim, p_ok], include_eliminated=True)
    assert len(ranked) == 2
    # Eliminated at the bottom (fitness 0).
    assert ranked[-1][0].program_id == "p_elim"


def test_rank_programs_empty_returns_empty() -> None:
    student = StudentFeatures(sparse={"education_level": "bachelors"})
    assert rank_programs(student, []) == []
