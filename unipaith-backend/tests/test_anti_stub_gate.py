"""Enforced anti-stub gate for certified-clean program catalogs (enrich-profile §8.5).

``check_conformance`` is presence-only and cannot see a stubbed description, so eight
consecutive stub-swap "repair" PRs auto-merged through green CI (REPAIR_BACKLOG run 55).
This test closes that hole: every catalog in ``CERTIFIED_CLEAN`` must score the same
zero the gold MIT reference does on the ``anti_stub`` description-quality metrics, so a
stub-swap of a certified catalog FAILS CI and cannot auto-merge.

To certify a newly de-fabricated catalog, add it to ``CERTIFIED_CLEAN`` — CI then
re-computes the metrics and blocks the merge unless the rows are genuinely researched
per-program. The thresholds are NOT tunable: a non-zero is the no-fabrication /
structure-before-depth invariant, not a knob.
"""

import importlib

import pytest

from unipaith.profile_standard.anti_stub import analyze

# Catalogs whose per-program descriptions have been verified gold-equal (every metric 0).
# Grow this list as catalogs are genuinely de-fabricated — never weaken the assertions.
CERTIFIED_CLEAN = [
    "mit",        # gold reference
    "ucsd",       # cert padding dropped; per-credential descriptions (#745 + this run)
    "caltech",    # cert + non-terminal-MS padding dropped; field-specific descriptions (this run)
    "nyu",        # bulletin-sourced descriptions; school-blurb + synthesized reviews removed (#753)
    "princeton",  # CIP rollups → real majors; textbook-def stubs → researched descriptions (#754)
    "carnegie_mellon",  # researched per-program clauses; "{program_name}: " prefix-double removed
    "duke",       # "{program_name}: " prefix-double removed; per-credential doctoral clauses
    "uiuc",       # catalogue-sourced descriptions; school-blurb + synthesized reviews removed
    "usc",        # catalogue-sourced descriptions; school-blurb + synthesized reviews removed
    "michigan",   # catalogue-sourced descriptions; school-blurb + synthesized reviews removed
    "georgia_tech",  # catalog.gatech.edu descriptions; stubs + synth reviews removed (gatechprof3)
    "ut_austin",  # catalog.utexas.edu descriptions; school-blurb + synth reviews removed (utaprof2)
    "ucla",       # catalogue-sourced descriptions; school-blurb + synthesized reviews removed
    "uw",         # catalogue-sourced descriptions; school-blurb + synth reviews removed (uwprof2)
    "jhu",        # per-credential field clauses; verbatim-across-levels removed
    "stanford",   # catalogue descriptions; rollup names + synth reviews removed
]


def _programs(name: str) -> list[dict]:
    mod = importlib.import_module(f"unipaith.data.{name}_profile")
    return list(getattr(mod, "PROGRAMS", []))


@pytest.mark.parametrize("name", CERTIFIED_CLEAN)
def test_certified_catalog_is_anti_stub_clean(name: str):
    report = analyze(_programs(name))
    assert report.is_clean, (
        f"{name} catalog is no longer anti-stub clean: {report.summary()}\n"
        + "\n".join(
            f"  {metric}: {items[:5]}{' …' if len(items) > 5 else ''}"
            for metric, items in report.violations.items()
            if items
        )
    )


def test_gold_mit_is_the_zero_baseline():
    """MIT — the gold reference — must score zero on every metric (the baseline)."""
    report = analyze(_programs("mit"))
    assert report.is_clean, f"gold MIT regressed: {report.summary()}"


def test_analyzer_detects_a_school_blurb_stub_catalog():
    """Regression guard: the gate must BITE on the school-blurb fabrication form."""
    blurb = (
        "Example University's {field} program connects to the College of Arts and "
        "Sciences, the university's largest college spanning the humanities, social "
        "sciences, and natural sciences.. Students build depth in {field} through "
        "seminars, research, and city industry and community partnerships."
    )
    fabricated = [
        {"program_name": f"Bachelor of Arts in {fld}", "description": blurb.format(field=fld)}
        for fld in ("Anthropology", "Classics", "Economics", "History")
    ]
    report = analyze(fabricated)
    assert not report.is_clean
    assert report.double_period, "should flag the '..' splice"
    assert report.cross_field_clause, "should flag one body stamped across different fields"


def test_cross_field_clause_is_case_insensitive_on_the_field_token():
    """The school-blurb stamp often lowercases the interpolated field token
    ("anthropology program connects…") while program_name is title-cased
    ("… in Anthropology"). The cross-field neutralization must be case-insensitive,
    or a lowercase-field blurb with no '..'/classification tell would pass as clean.
    """
    # No double-period and no classification phrase — the cross-field clause is the
    # ONLY tell, and the field token is lowercase in the body (mismatching the title-
    # cased name), so a case-sensitive normalization would miss it.
    blurb = (
        "At Example University, {field_lc} students join a research collective that "
        "spans the humanities and social sciences, building methodological depth "
        "through seminars and faculty-led projects across the city's institutions."
    )
    fabricated = [
        {
            "program_name": f"Bachelor of Arts in {fld}",
            "description": blurb.format(field_lc=fld.lower()),
        }
        for fld in ("Anthropology", "Classics", "Economics", "History")
    ]
    report = analyze(fabricated)
    assert not report.double_period, "guard premise: this fixture has no '..' tell"
    assert report.cross_field_clause, (
        "case-insensitive field neutralization must still flag one body stamped "
        "across different fields when the body lowercases the field token"
    )


def test_analyzer_detects_classification_and_prefix_stubs():
    fabricated = [
        {
            "program_name": "Bachelor of Science in Aerospace Engineering",
            "description": (
                "Bachelor of Science in Aerospace Engineering is an undergraduate major "
                "offered through Example University's College of Engineering."
            ),
        },
    ]
    report = analyze(fabricated)
    assert report.name_prefixed, "should flag the program_name-prefixed description"
    assert report.classification, "should flag the classification-only description"
