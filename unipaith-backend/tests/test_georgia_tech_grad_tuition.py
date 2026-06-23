"""Georgia Tech profile — professional-tier tuition coverage (REPAIR_BACKLOG)."""

from unipaith.data import georgia_tech_profile as p


def _effective_cost(spec: dict) -> dict:
    override = p._COST_BY_SLUG.get(spec["slug"])
    if override is not None:
        return override
    return p._grad_cost(spec)


def test_professional_tier_carries_published_tuition():
    """Every professional program must carry verified tuition — not matcher-blind nulls."""
    for spec in p.PROGRAMS:
        if spec["degree_type"] != "professional":
            continue
        cost = _effective_cost(spec)
        assert cost.get("tuition_usd") is not None, spec["slug"]
        assert cost["tuition_usd"] != p._TUITION_UG_IN_STATE, spec["slug"]


def test_professional_tuition_rates_are_distinct():
    """Professional schools bill their own rates — no undergrad copy-down."""
    prof_rates = {
        _effective_cost(spec)["tuition_usd"]
        for spec in p.PROGRAMS
        if spec["degree_type"] == "professional"
    }
    assert len(prof_rates) >= 4
    assert p._TUITION_UG_IN_STATE not in prof_rates


def test_executive_and_gtpe_programs_stamp_total_program_fees():
    """Executive MBA and GTPE professional master's carry published total-program figures."""
    expected = {
        "gatech-mba-global-business-executive": 87100,
        "gatech-mba-management-technology-executive": 87100,
        "gatech-applied-systems-engineering-pmase": 34150,
        "gatech-manufacturing-leadership-pmml": 34150,
        "gatech-occupational-safety-health-pmosh": 34150,
    }
    for slug, amount in expected.items():
        cost = p._COST_BY_SLUG[slug]
        assert cost["tuition_usd"] == amount
        assert cost["tuition_basis"] == "total program"
