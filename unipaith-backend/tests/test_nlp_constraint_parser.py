"""Unit tests for the rule-based NL query constraint parser (G-S3 / G-AI6).

The parser turns a free-text Discovery query into typed constraints that the
frontend renders as individually-editable chips. It must work with no LLM (the
AI_MOCK / deterministic-fallback path), so these tests assert the extraction
contract directly.
"""

from unipaith.services.institution_service import _rule_based_query_parse


def test_extracts_degree_subject_location_budget_format():
    out = _rule_based_query_parse("MS in Computer Science in California under $50k online")
    assert out["degree_type"] == "masters"
    assert out["subjects"] == "Computer Science"
    assert out["country"] == "United States"
    assert out["region"] == "California"
    assert out["max_tuition"] == 50000
    assert out["delivery_format"] == "online"
    # parsed_query is the keyword remainder fed to full-text search
    assert "computer science" in out["parsed_query"].lower()


def test_phd_and_cheapest_sort():
    out = _rule_based_query_parse("cheapest PhD in data science")
    assert out["degree_type"] == "phd"
    assert out["sort_by"] == "tuition_asc"
    assert out["subjects"] == "Data Science"


def test_mba_maps_to_masters():
    out = _rule_based_query_parse("MBA programs under 40k")
    assert out["degree_type"] == "masters"
    assert out["max_tuition"] == 40000


def test_bare_thousands_normalized():
    # "under 60" in a tuition context means 60,000, not 60
    out = _rule_based_query_parse("masters under 60")
    assert out["max_tuition"] == 60000


def test_uk_country_alias():
    out = _rule_based_query_parse("bachelor's in economics in the UK")
    assert out["degree_type"] == "bachelors"
    assert out["country"] == "United Kingdom"
    assert "economics" in out["subjects"].lower()


def test_plain_query_has_no_spurious_constraints():
    out = _rule_based_query_parse("biology")
    assert "degree_type" not in out
    assert "max_tuition" not in out
    assert "country" not in out
    assert out["parsed_query"] == "biology"


def test_interpretation_is_human_readable():
    out = _rule_based_query_parse("MS in Computer Science under $50k")
    assert out["interpretation"].startswith("Showing")
    assert "master's" in out["interpretation"]
    assert "$50,000" in out["interpretation"]
