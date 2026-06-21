"""Priority sliders actually re-rank under CPEF (pipeline audit #11).

Before this, weights_from_preferences was computed and threaded all the way to
score() then silently DROPPED under CPEF (score() called _score_cpef without
params), so 5 of 6 priority sliders changed nothing. Now slider-derived per-signal
weights (params["w_<signal>"]) thread through rank_programs → score → _score_cpef →
cpef → _build_cpef_signals, so a cost-heavy vs location-heavy student genuinely sees
a different ranking. Backward-compatible: no params → uniform w_base (unchanged).
Pure, no DB.
"""

from unipaith.services.match.params import DEFAULT_PARAMS
from unipaith.services.matching import ProgramFeatures, StudentFeatures, rank_programs


def test_slider_params_reorder_results_under_cpef() -> None:
    student = StudentFeatures(
        sparse={"budget_max_usd_per_year": 30000, "geo_must": ["USA"]},
        extractor_quality=0.7,
    )
    # local_pricey: perfect geo, weak budget fit (over budget, within veto tolerance).
    local_pricey = ProgramFeatures(
        program_id="local",
        sparse={"locations": ["USA"], "tuition_usd_per_year": 35000},
        data_completeness=0.6,
    )
    # cheap_farflung: weak geo (disjoint), perfect budget fit (well under budget).
    cheap_farflung = ProgramFeatures(
        program_id="cheap",
        sparse={"locations": ["UK"], "tuition_usd_per_year": 15000},
        data_completeness=0.6,
    )
    progs = [local_pricey, cheap_farflung]

    cost_heavy = {**DEFAULT_PARAMS, "w_budget": 9.5}
    loc_heavy = {**DEFAULT_PARAMS, "w_geo": 9.5}

    cost_ranked = rank_programs(student, progs, params=cost_heavy, cpef_enabled=True)
    loc_ranked = rank_programs(student, progs, params=loc_heavy, cpef_enabled=True)
    cost_rank = [p.program_id for p, _ in cost_ranked]
    loc_rank = [p.program_id for p, _ in loc_ranked]

    assert cost_rank[0] == "cheap"  # cost-heavy → the cheap program wins
    assert loc_rank[0] == "local"  # location-heavy → the well-located program wins
    assert cost_rank != loc_rank  # the sliders genuinely re-rank


def test_no_params_is_unchanged_uniform_weights() -> None:
    # Backward-compat: with no params the per-signal weight is the uniform w_base,
    # so ranking is identical to the pre-change behavior (the tuned suite relies on this).
    student = StudentFeatures(sparse={"interest_themes": ["ml"]}, extractor_quality=0.7)
    progs = [
        ProgramFeatures(program_id="a", sparse={"interest_themes": ["ml"]}, data_completeness=0.6),
        ProgramFeatures(program_id="b", sparse={"interest_themes": ["bio"]}, data_completeness=0.6),
    ]
    ranked = rank_programs(student, progs, cpef_enabled=True)
    assert [p.program_id for p, _ in ranked][0] == "a"  # the matching program leads


def test_cpef_params_from_preferences_maps_set_sliders() -> None:
    from types import SimpleNamespace

    from unipaith.services.match_banding import cpef_params_from_preferences

    w_base = DEFAULT_PARAMS["w_base"]
    pref = SimpleNamespace(
        weight_cost=10,
        weight_location=0,
        weight_flexibility=None,
        weight_support=None,
        weight_time_to_degree=None,
    )
    params = cpef_params_from_preferences(pref)
    assert params is not None
    assert params["w_budget"] > w_base  # cost slider maxed → budget signal boosted
    assert params["w_geo"] < w_base  # location slider zeroed → geo signal reduced
    assert "w_flexibility" not in params  # unset slider → no override
    assert "alpha" in params and "kappa" in params  # full params dict preserved


def test_cpef_params_none_when_no_sliders_set() -> None:
    from types import SimpleNamespace

    from unipaith.services.match_banding import cpef_params_from_preferences

    assert cpef_params_from_preferences(None) is None
    blank = SimpleNamespace(
        weight_cost=None,
        weight_location=None,
        weight_flexibility=None,
        weight_support=None,
        weight_time_to_degree=None,
    )
    assert cpef_params_from_preferences(blank) is None
