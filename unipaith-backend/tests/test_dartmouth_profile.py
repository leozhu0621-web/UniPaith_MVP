"""Dartmouth profile — matcher-core + universal-depth gates.

Covers the 2026-06-25 finish pass: full Guarini graduate catalog (breadth), `cip_code`
on every program (REPAIR_BACKLOG #1), `who_its_for` on every program (#4), graduate-tier
tuition with honest omits (#3/#4), and the anti-stub baseline (gold MIT = 0).
"""

from unipaith.data import dartmouth_profile as p
from unipaith.profile_standard.anti_stub import (
    analyze,
    frame_stripped_shared_body,
    machine_artifacts,
    scrape_debris,
    template_slot_artifacts,
)

# Master's with no payable tuition figure: the three Guarini-FUNDED master's (Earth
# Sciences MS, Comparative Literature MA, Sonic Practice MFA) receive the full PhD-style
# funding package, so they carry funded=True + tuition=None rather than a sticker. Every
# other master's (incl. the Geisel health master's + MET) carries its published rate.
_TUITION_OMITTED_MASTERS = {
    "dartmouth-earth-sciences-ms",
    "dartmouth-comparative-literature-ms",
    "dartmouth-sonic-practice-ms",
}


def test_graduate_tiers_carry_published_or_honestly_omitted_tuition():
    """Filled master's/professional carry a school-distinct published rate (never the
    undergrad sticker); the omit-set carries no fabricated figure; PhDs are funded-omit."""
    for spec in p.PROGRAMS:
        dtype, slug = spec["degree_type"], spec["slug"]
        if dtype in ("masters", "professional"):
            if slug in _TUITION_OMITTED_MASTERS:
                assert not p._grad_has_verified_tuition(spec), slug
            else:
                assert p._grad_has_verified_tuition(spec), slug
                cost = p._COST_BY_SLUG[slug]
                assert cost.get("tuition_usd") is not None, slug
                assert cost["tuition_usd"] != p._TUITION_UG, slug
        elif dtype == "phd":
            assert not p._grad_has_verified_tuition(spec), slug


def test_graduate_tuition_rates_are_distinct_no_undergrad_copydown():
    """Each school bills its own rate — no undergrad sticker copied down the grad tree."""
    rates = {p._COST_BY_SLUG[s]["tuition_usd"] for s in p._COST_BY_SLUG}
    assert len(rates) >= 5
    assert p._TUITION_UG not in rates


def test_every_program_carries_cip_code():
    """Matcher-core: cip_code on every program (REPAIR_BACKLOG #1), valid NN.NN family."""
    for spec in p.PROGRAMS:
        cip = p._CIP_BY_SLUG.get(spec["slug"])
        assert cip, spec["slug"]
        head, _, tail = cip.partition(".")
        assert head.isdigit() and tail.isdigit() and len(tail) == 2, (spec["slug"], cip)


def test_every_program_carries_who_its_for_not_a_stub():
    """Universal depth: who_its_for on every program (REPAIR_BACKLOG #4), gold-contrast
    (no "for students interested in {field}" classification stub)."""
    for spec in p.PROGRAMS:
        who = p._WHO_BY_SLUG.get(spec["slug"])
        assert who and len(who) > 40, spec["slug"]
        # The forbidden classification stub is "for students interested in {field}".
        assert "for students interested in" not in who.lower(), spec["slug"]


def test_catalog_breadth_and_distinct_names():
    """The full Guarini catalog is present (peer breadth) with no duplicate rendered names."""
    assert len(p.PROGRAMS) >= 60, len(p.PROGRAMS)
    seen = set()
    for spec in p.PROGRAMS:
        key = (spec["program_name"], spec["degree_type"])
        assert key not in seen, key
        seen.add(key)


def test_catalog_is_anti_stub_clean():
    """Descriptions score 0 on every enforced anti-stub metric (gold MIT baseline)."""
    progs = p.PROGRAMS
    assert analyze(progs).is_clean, analyze(progs).summary()
    assert not machine_artifacts(progs)
    assert not template_slot_artifacts(progs)
    assert not scrape_debris(progs)
    assert not frame_stripped_shared_body(progs, abs_chars=150)
