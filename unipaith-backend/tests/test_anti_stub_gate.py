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

from unipaith.profile_standard.anti_stub import analyze, machine_artifacts

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
    "georgia_tech",  # catalog.gatech.edu descriptions; stubs + synth reviews removed (gatechprof3)
    "ut_austin",  # catalog.utexas.edu descriptions; school-blurb + synth reviews removed (utaprof2)
    "uw",         # Wikipedia-sourced per-credential descriptions; junk/Westwood removed (uwdefab1)
    "ucla",       # Wikipedia per-credential descriptions; Catalog entry junk removed (uclaprof4)
    "jhu",        # per-credential field clauses (verbatim-across-levels removed); real reviews kept
    "michigan",   # per-credential discipline definitions; build-artifact junk removed (michprof4)
    "stanford",   # per-credential defs; Catalog entry junk removed (stanfordprof11)
    "purdue",     # per-credential discipline defs; peer-copy + rollups removed (purduedefab1)
    "chicago",    # per-credential graduate descriptions; cert padding dropped (chicagodefab1)
    "bu",         # Medill peer-copy removed; real dual-degree/MPH/CFA/math/world-lang
    #             names + depts; per-credential bodies; school-as-field fixes (budefab1,
    #             supersedes buprof11's narrower description-only repair)
    "berkeley",   # CIP rollup de-fab; real dept names; per-credential descriptions (berkeleyprof9)
    "cornell",    # CIP-rollup buckets → real Cornell degrees or dropped; field-echo
    #             departments → real owning college; per-credential description leads
    #             (verbatim/shared-body removed) (cornelldefab1)
    # NOTE: stanford was REMOVED briefly (2026-06-18, uwdefab1) while it still shipped build-script
    # junk; re-added after stanfordprof11 regeneration matching Michigan/UW repair model.
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


@pytest.mark.parametrize("name", CERTIFIED_CLEAN)
def test_certified_catalog_has_no_machine_artifacts(name: str):
    """A certified catalog must not render build-script junk (e.g. "Catalog entry <hex>:"
    or a raw hex id) — these pass every description-quality metric yet show raw junk to
    students. Three certified catalogs (UW/Michigan/UCLA) shipped this live; the gate
    closes that hole (REPAIR_BACKLOG run 59)."""
    hits = machine_artifacts(_programs(name))
    assert not hits, (
        f"{name} catalog carries machine-build artifacts in {len(hits)} descriptions: "
        f"{hits[:5]}{' …' if len(hits) > 5 else ''}"
    )


def test_artifact_detector_bites_on_catalog_entry_junk():
    """Regression guard: the artifact gate must flag the live "Catalog entry <hex>:" form
    while passing a clean field-specific description."""
    junk = [
        {
            "program_name": "Bachelor of Arts in Accounting",
            "description": (
                "Catalog entry 5686776b4e64: Catalog entry 5686776b4e64: UW's Foster "
                "School of Business draws on the Department of Finance on the Westwood campus."
            ),
        }
    ]
    clean = [
        {
            "program_name": "Bachelor of Arts in Accounting",
            "description": (
                "Accounting is the process of recording and processing information about "
                "economic entities. At the University of Washington's Foster School of "
                "Business in Seattle, this program engages the discipline."
            ),
        }
    ]
    assert machine_artifacts(junk), "should flag the 'Catalog entry <hex>' junk"
    assert not machine_artifacts(clean), "must not flag a clean field-specific description"


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


def test_nyu_catalog_has_no_slug_leak_prefixes():
    """Regression guard: kebab-case bulletin slugs must not prefix description_text
    (REPAIR_BACKLOG CRITICAL #2 — invisible to machine_artifacts, visible to students)."""
    import re

    from unipaith.data import nyu_profile

    slug_re = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s")
    hits = [
        p["slug"]
        for p in nyu_profile.PROGRAMS
        if slug_re.match((p.get("description") or "").strip())
    ]
    assert not hits, (
        f"NYU catalog has {len(hits)} slug-prefixed descriptions: {hits[:5]}"
    )
