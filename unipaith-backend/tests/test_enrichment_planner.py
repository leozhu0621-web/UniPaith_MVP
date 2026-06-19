"""Slice C — enrichment planner (Spec 1). Pure, no DB."""

from unipaith.services.enrichment_planner import (
    CATALOG,
    ESSENTIAL_KEYS,
    SECTION_FIELDS,
    action_for,
    essentials_present,
    plan_next,
)


def test_action_for_each_tier():
    assert action_for(None) == "ask"  # missing
    assert action_for({"value": "x", "confidence": None}) == "confirm"  # unattributed
    assert action_for({"value": "x", "confidence": 0.95}) == "skip"  # confirmed
    assert action_for({"value": "x", "confidence": 0.7}) == "confirm"  # imported
    assert action_for({"value": "x", "confidence": 0.3}) == "ask"  # inferred/weak
    assert action_for({"value": "", "confidence": 0.95}) == "ask"  # empty value


def test_empty_state_asks_essentials_first():
    items = plan_next({}, limit=3)
    assert len(items) == 3
    assert all(i["tier"] == "essential" for i in items)
    assert all(i["action"] == "ask" for i in items)
    assert items[0]["field"] in ESSENTIAL_KEYS


def test_limit_respected():
    assert len(plan_next({}, limit=5)) == 5
    assert len(plan_next({}, limit=0)) == 0


def test_confirmed_essentials_are_skipped_then_high_value_surfaces():
    state = {k: {"value": "x", "confidence": 0.95} for k in ESSENTIAL_KEYS}
    items = plan_next(state, limit=3)
    # all essentials solid → next priority is high-value gaps
    assert all(i["tier"] == "high_value" for i in items)


def test_ask_before_confirm_within_tier():
    # one essential imported (→confirm), the rest missing (→ask): asks come first
    state = {"gender": {"value": "f", "confidence": 0.7}}
    items = plan_next(state, limit=10)
    essential_items = [i for i in items if i["tier"] == "essential"]
    actions = [i["action"] for i in essential_items]
    # every "ask" precedes every "confirm"
    assert actions == sorted(actions, key=lambda a: 0 if a == "ask" else 1)
    assert "confirm" in actions  # the imported gender


def test_essentials_present():
    assert essentials_present({}) is False
    full = {k: {"value": "x", "confidence": 0.4} for k in ESSENTIAL_KEYS}
    assert essentials_present(full) is True  # present regardless of confidence
    missing_one = dict(full)
    del missing_one[ESSENTIAL_KEYS[0]]
    assert essentials_present(missing_one) is False


def test_ranking_weight_excluded_from_catalog():
    assert all("ranking" not in f["key"] for f in CATALOG)


def test_weight_fields_use_scale_widget():
    weights = [f for f in CATALOG if f["type"] == "weight"]
    assert weights and all(f["ask_kind"] == "scale" for f in weights)


# ── Ship 2: section scoping ──────────────────────────────────────────────


def test_section_fields_keys_all_exist_in_catalog():
    catalog_keys = {f["key"] for f in CATALOG}
    for section, keys in SECTION_FIELDS.items():
        assert keys, f"{section} has no fields"
        for k in keys:
            assert k in catalog_keys, f"{section}: '{k}' is not a CATALOG key"


def test_section_goals_only_returns_goals():
    # empty state → every goals candidate is the only thing that can surface
    items = plan_next({}, limit=10, section="goals")
    assert items, "goals section should surface its pending signal"
    assert {i["field"] for i in items} == {"goals"}


def test_section_preferences_only_returns_preferences_fields():
    items = plan_next({}, limit=20, section="preferences")
    expected = set(SECTION_FIELDS["preferences"])
    fields = {i["field"] for i in items}
    assert fields, "preferences section should surface pending signals"
    assert fields <= expected
    # the contract's preferences fields are exactly weight_*/budget_band/
    # preferred_countries/funding_requirement — nothing else may leak in
    for f in fields:
        assert f.startswith("weight_") or f in {
            "budget_band",
            "preferred_countries",
            "funding_requirement",
        }, f"unexpected field '{f}' in preferences section"


def test_section_scoping_preserves_ranking_order():
    # within preferences, high-value (budget/countries/weight_cost/...) precede
    # standard (weight_flexibility/support/time_to_degree, funding_requirement)
    items = plan_next({}, limit=20, section="preferences")
    tiers = [i["tier"] for i in items]
    rank = {"essential": 0, "high_value": 1, "standard": 2}
    assert [rank[t] for t in tiers] == sorted(rank[t] for t in tiers)


def test_unknown_section_is_unchanged_global_next():
    base = plan_next({}, limit=3)
    assert plan_next({}, limit=3, section="not-a-section") == base


def test_none_section_is_unchanged_global_next():
    base = plan_next({}, limit=5)
    assert plan_next({}, limit=5, section=None) == base
    # explicit default call is identical too
    assert plan_next({}, limit=5) == base
