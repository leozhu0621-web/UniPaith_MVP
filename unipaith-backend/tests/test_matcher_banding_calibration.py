"""Founder-greenlit banding/confidence calibration (audit batch D).

Two changes, both about how the matcher's numbers reach the student's
admission-odds display:

- Rank 10: probability-band VISIBILITY gates on the student-side confidence
  (c_student) — "do we know the STUDENT well enough to estimate her odds" — not the
  program-authority-diluted product. Band WIDTH still uses the product confidence.
- Rank 8: bands are computed from the student-direction fit (s2p_value), not the
  alpha-inflated blend M (which over-bands no-preference programs).

(The audit's Rank 12 coverage-breadth change is deferred — its naive form also
stripped coverage's c_student dependence, weakening the central deeper-profile
property; it needs a surgical redesign. See test_ai_structure_cohort.)

Pure, no DB.
"""

import pytest

from unipaith.ai.probability import estimate_probability_bands
from unipaith.services.matching import (
    ProgramFeatures,
    StudentFeatures,
    cpef,
    score,
)

# ── coverage breadth (sanity — independent of the deferred Rank 12) ──────────


def test_coverage_still_rises_with_more_present_dimensions() -> None:
    # Breadth still matters: a program matching on more present dimensions reads
    # as more covered than one matching on fewer.
    student = StudentFeatures(
        sparse={
            "interest_themes": ["ml"],
            "needs_signals": {"funding": 1.0},
            "field_of_study": "data_science",
            "gpa": 3.6,
        },
        extractor_quality=0.7,
    )
    thin = ProgramFeatures(program_id="thin", sparse={"interest_themes": ["ml"]})
    broad = ProgramFeatures(
        program_id="broad",
        sparse={
            "interest_themes": ["ml"],
            "support_signals": {"funding": 1.0},
            "fields_offered": ["data_science"],
            "pref_min_gpa": 3.0,
        },
    )
    assert cpef(student, broad)[1]["coverage"] > cpef(student, thin)[1]["coverage"]


# ── Rank 10a: c_student exposed in the CPEF confidence breakdown ──────────────


def test_cpef_confidence_breakdown_exposes_c_student() -> None:
    student = StudentFeatures(sparse={"interest_themes": ["ml"]}, extractor_quality=0.7)
    program = ProgramFeatures(
        program_id="p", sparse={"interest_themes": ["ml"]}, data_completeness=0.5
    )
    sc = score(student, program, cpef_enabled=True)
    assert sc.confidence_breakdown["c_student"] == pytest.approx(0.7, abs=0.01)


# ── Rank 10b: band visibility gates on readiness; width on product ───────────


def test_bands_gate_on_readiness_not_product_confidence() -> None:
    # A solid student (readiness 0.6) against a low-authority program (product
    # confidence 0.24, below the 0.30 gate) STILL gets bands.
    no_readiness = estimate_probability_bands(acceptance_rate=0.5, fitness=0.6, confidence=0.24)
    assert no_readiness is None  # back-compat: no readiness → gate on the product
    with_readiness = estimate_probability_bands(
        acceptance_rate=0.5, fitness=0.6, confidence=0.24, readiness=0.6
    )
    assert with_readiness is not None  # readiness clears the gate
    thin = estimate_probability_bands(
        acceptance_rate=0.5, fitness=0.6, confidence=0.24, readiness=0.2
    )
    assert thin is None  # a genuinely thin student is still gated out


def test_band_width_still_uses_product_confidence() -> None:
    # Same readiness, lower PRODUCT confidence → wider band (program-data uncertainty).
    narrow = estimate_probability_bands(
        acceptance_rate=0.5, fitness=0.6, confidence=0.9, readiness=0.7
    )
    wide = estimate_probability_bands(
        acceptance_rate=0.5, fitness=0.6, confidence=0.3, readiness=0.7
    )
    nw = narrow["admit"]["high"] - narrow["admit"]["low"]
    ww = wide["admit"]["high"] - wide["admit"]["low"]
    assert ww > nw


# ── Rank 8: band the student-direction fit (s2p_value), not the blend M ──────


def test_band_fitness_prefers_s2p_value_over_blended_m() -> None:
    from types import SimpleNamespace

    from unipaith.api.students import _band_fitness

    # M (fitness_score) is alpha-inflated above the student's own fit s2p_value.
    match = SimpleNamespace(fitness_score=0.62, fitness_breakdown={"s2p_value": 0.5, "m": 0.62})
    assert _band_fitness(match) == 0.5
    # no s2p_value (legacy / non-cpef) → fall back to the persisted fitness_score
    legacy = SimpleNamespace(fitness_score=0.62, fitness_breakdown={})
    assert _band_fitness(legacy) == 0.62
    legacy_none = SimpleNamespace(fitness_score=0.62, fitness_breakdown=None)
    assert _band_fitness(legacy_none) == 0.62
