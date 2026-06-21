"""Student-facing 'drivers' phrasing for the stub rationale.

The explain-match stub builds a qualitative "driven by ..." phrase. For a CPEF
breakdown the raw keys are internal (model/value/inner/coverage/veto/mean_rho/
signals/...), so the phrase MUST be built from the per-signal list mapped to
plain labels — never the raw breakdown keys. Pure helper, no DB.
"""

from unipaith.api.students import _humanize_fitness_drivers

_INTERNAL_KEYS = {
    "model",
    "value",
    "inner",
    "coverage",
    "veto",
    "hard_floor",
    "mean_rho",
    "coverage_sum",
    "raw_fit_sum",
    "signals",
    "dealbreakers",
    "m",
    "s2p_value",
    "p2s",
    "alpha",
    "weights",
    "nominal_weights",
    "cosine_applied",
}


def test_cpef_breakdown_maps_top_signals_to_friendly_labels() -> None:
    bd = {
        "model": "cpef",
        "value": 0.71,
        "inner": 0.8,
        "coverage": 0.9,
        "signals": [
            {"key": "themes", "f": 0.9},
            {"key": "needs", "f": 0.4},
            {"key": "budget", "f": 0.85},
            {"key": "geo", "f": 0.1},
        ],
    }
    drivers = _humanize_fitness_drivers(bd, top_n=3)
    # strongest-f signals first → themes(0.9), budget(0.85), needs(0.4)
    assert drivers == ["interests & goals", "affordability", "your priorities"]


def test_cpef_breakdown_never_leaks_internal_keys() -> None:
    bd = {
        "model": "cpef",
        "inner": 0.8,
        "coverage": 0.9,
        "veto": 1.0,
        "mean_rho": 0.3,
        "signals": [{"key": "semantic", "f": 0.7}],
    }
    drivers = _humanize_fitness_drivers(bd)
    assert all(d not in _INTERNAL_KEYS for d in drivers)
    assert "academic interests" in drivers


def test_legacy_breakdown_maps_components_and_drops_meta_keys() -> None:
    bd = {
        "cosine": 0.6,
        "soft_align": 0.5,
        "needs_match": 0.4,
        "cosine_applied": False,
        "weights": {"soft_align": 0.6},
        "nominal_weights": {"cosine": 0.45},
    }
    drivers = _humanize_fitness_drivers(bd)
    assert all(d not in _INTERNAL_KEYS for d in drivers)
    assert "interests & goals" in drivers
    assert "your priorities" in drivers


def test_empty_or_garbage_returns_empty() -> None:
    assert _humanize_fitness_drivers({}) == []
    assert _humanize_fitness_drivers({"model": "cpef", "signals": []}) == []
    assert _humanize_fitness_drivers(None) == []  # type: ignore[arg-type]
