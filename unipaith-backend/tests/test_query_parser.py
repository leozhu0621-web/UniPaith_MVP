"""Unit tests for the rule-based query parser (spec 10 §15).

Pure functions — no DB, no network. Validates the deterministic NL → chip
extraction that is both the flag-off default and the LLM fallback.
"""

from unipaith.schemas.search import ConstraintCategory
from unipaith.services.query_parser import parse_query


def _by_cat(chips):
    return {c.category: c for c in chips}


def test_ms_cs_california_budget_startterm():
    """Spec 10 §15: 'MS CS in California under $50k' yields degree, location,
    budget chips (we additionally surface major + start_term)."""
    chips = parse_query("MS in Computer Science in California under $50k starting fall 2027")
    by = _by_cat(chips)
    assert ConstraintCategory.degree_level in by
    assert ConstraintCategory.location in by
    assert ConstraintCategory.budget in by
    assert by[ConstraintCategory.degree_level].value == "master"
    assert by[ConstraintCategory.budget].value == "<=50000"
    assert by[ConstraintCategory.location].value.lower().startswith("california")
    # bonus extractions
    assert by[ConstraintCategory.major].value == "computer science"
    assert by[ConstraintCategory.start_term].value == "fall 2027"


def test_affordable_online_nursing():
    chips = parse_query("affordable online nursing programs")
    by = _by_cat(chips)
    assert by[ConstraintCategory.format].value == "online"
    assert by[ConstraintCategory.major].value == "nursing"
    # "affordable" with no number → low-confidence budget chip (prompts confirm).
    assert by[ConstraintCategory.budget].confidence < 70


def test_budget_range():
    chips = parse_query("data science programs between $20k and $50k")
    by = _by_cat(chips)
    assert by[ConstraintCategory.budget].value == "20000-50000"


def test_duration_range():
    chips = parse_query("1-2 year master's in data science")
    by = _by_cat(chips)
    assert by[ConstraintCategory.duration].value == "12-24"


def test_selectivity_highly():
    chips = parse_query("highly selective computer science master's")
    by = _by_cat(chips)
    assert by[ConstraintCategory.selectivity].value == "very_high"


def test_phd_degree():
    chips = parse_query("PhD in bioengineering")
    by = _by_cat(chips)
    assert by[ConstraintCategory.degree_level].value == "doctorate"


def test_empty_query_returns_no_chips():
    assert parse_query("") == []
    assert parse_query("   ") == []


def test_chip_has_deterministic_id():
    chips = parse_query("online mba")
    for c in chips:
        assert c.id == f"{c.category.value}:{c.value}".lower()
