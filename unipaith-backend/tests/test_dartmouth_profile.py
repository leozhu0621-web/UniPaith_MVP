"""Dartmouth profile — graduate-tier tuition coverage (REPAIR_BACKLOG #4)."""

from unipaith.data import dartmouth_profile as p


def test_graduate_tiers_carry_published_tuition():
    """Master's/professional tiers must carry school-distinct published tuition."""
    for spec in p.PROGRAMS:
        dtype = spec["degree_type"]
        if dtype in ("masters", "professional"):
            assert p._grad_has_verified_tuition(spec), spec["slug"]
            cost = p._COST_BY_SLUG[spec["slug"]]
            assert cost.get("tuition_usd") is not None, spec["slug"]
            assert cost["tuition_usd"] != p._TUITION_UG, spec["slug"]
        elif dtype == "phd":
            assert not p._grad_has_verified_tuition(spec), spec["slug"]


def test_graduate_tuition_rates_are_distinct():
    """Each school bills its own rate — no undergrad copy-down."""
    rates = {p._COST_BY_SLUG[s]["tuition_usd"] for s in p._COST_BY_SLUG}
    assert len(rates) >= 5
    assert p._TUITION_UG not in rates
