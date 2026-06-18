"""Slice C — enrichment planner (Spec 1). Pure, no DB."""

from unipaith.services.enrichment_planner import (
    CATALOG,
    ESSENTIAL_KEYS,
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
