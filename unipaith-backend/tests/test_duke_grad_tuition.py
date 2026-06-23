"""Duke profile — professional-tier tuition coverage (REPAIR_BACKLOG #4)."""

from unipaith.data import duke_profile as p


def test_professional_tier_carries_published_tuition():
    """Every professional program must carry school-distinct published tuition."""
    for spec in p.PROGRAMS:
        if spec["degree_type"] != "professional":
            continue
        assert p._grad_has_verified_tuition(spec), spec["slug"]
        cost = p._COST_BY_SLUG.get(spec["slug"])
        assert cost is not None, spec["slug"]
        assert cost.get("tuition_usd") is not None, spec["slug"]
        assert cost["tuition_usd"] != p._TUITION_UG, spec["slug"]


def test_professional_tuition_rates_are_distinct():
    """Professional schools bill their own rates — no undergrad copy-down."""
    prof_rates = {
        p._COST_BY_SLUG[s]["tuition_usd"]
        for s in p._COST_BY_SLUG
        if any(
            prog["slug"] == s and prog["degree_type"] == "professional"
            for prog in p.PROGRAMS
        )
    }
    assert len(prof_rates) >= 5
    assert p._TUITION_UG not in prof_rates
