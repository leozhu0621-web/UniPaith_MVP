"""Spec 10 §3 / Spec 45 §12 — rule-based DiscoveryQueryInterpreter unit tests.

Pure function (no DB / no I/O) so these run offline and guard the structured
constraints that the Spec 09 §5.1 / Spec 10 §4 editable chips depend on.
"""

from __future__ import annotations

from unipaith.services.institution_service import interpret_search_query


def test_degree_budget_and_keyword():
    r = interpret_search_query("Master's in Computer Science under $50k")
    assert r["degree_type"] == "masters"
    assert r["max_tuition"] == 50000
    # Degree + budget + noise words ("in") stripped; field-of-study keyword kept.
    assert r["parsed_query"] == "Computer Science"
    assert "Master's" in r["interpretation"]


def test_phd_detected_before_masters():
    r = interpret_search_query("PhD in bioengineering")
    assert r["degree_type"] == "phd"
    assert (r["parsed_query"] or "").lower() == "bioengineering"


def test_format_and_country():
    r = interpret_search_query("online data science in the United States")
    assert r["delivery_format"] == "online"
    assert r["country"] == "United States"
    assert (r["parsed_query"] or "").lower() == "data science"


def test_mba_maps_to_masters():
    r = interpret_search_query("MBA programs")
    assert r["degree_type"] == "masters"


def test_budget_dollar_without_trigger_word():
    r = interpret_search_query("design $30,000")
    assert r["max_tuition"] == 30000
    assert (r["parsed_query"] or "").lower() == "design"


def test_plain_keyword_has_no_constraints():
    r = interpret_search_query("computer science")
    assert r["degree_type"] is None
    assert r["max_tuition"] is None
    assert r["delivery_format"] is None
    assert r["country"] is None
    assert r["parsed_query"] == "computer science"


def test_empty_query_is_safe():
    r = interpret_search_query("")
    assert r["parsed_query"] is None
    assert r["interpretation"]
