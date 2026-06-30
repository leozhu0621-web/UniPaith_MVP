"""The WashU profile conforms to the gold standard for its institution, all eight of its
degree-granting schools, and its full 58-program catalog.

Pure (no DB): builds each node's persisted snapshot from the ``washu_profile`` module and runs
``check_conformance``. A node is accepted only when it is gold OR every remaining required field
is recorded in that node's ``_standard.omitted`` (verified-unavailable) with a real reason. Also
guards the matcher-side invariants: cip_code + who_its_for + a non-empty description on every
program; the whole bachelor's tier carries the published tuition sticker; no graduate row carries
the undergraduate sticker; the anti-stub gate is clean; and — the focus of the
master's-tuition-backfill repair (REPAIR_BACKLOG entry #1) — the master's tier carries the
published per-program annual rate (8 of 10 covered), with only the two Olin specialized master's
(flat program rate, no verifiable annual figure) honestly omitted-with-reason.
"""

# ruff: noqa: E501

from collections import defaultdict

from unipaith.data import washu_profile as w
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.anti_stub import (
    analyze,
    frame_stripped_shared_body,
    machine_artifacts,
    scrape_debris,
    template_slot_artifacts,
)

# The two Olin specialized master's are billed at a flat PER-PROGRAM rate published on each
# program's Olin Cost-Aid-Scholarships page; the 2026-06-30 pass researched those pages and
# now carries their published per-program rate (MS Finance $81,500; MS Business Analytics
# $67,866), closing the last master's-tier tuition null (REPAIR_BACKLOG entry #1).
_OLIN_FILLED = {"washu-finance-ms", "washu-business-analytics-ms"}


def _missing(level: str, snap: dict) -> list[str]:
    r = check_conformance(level, snap, profile_version=STANDARD_VERSION)
    return list(getattr(r, "missing_fields", []))


def _program_cost(spec: dict) -> dict:
    """Mirror ``washu_profile._apply_programs`` cost_data construction (the persisted shape)."""
    if spec["degree_type"] == "bachelors":
        return w._undergrad_cost()
    if spec.get("tuition") is not None:
        return {
            "tuition_usd": spec["tuition"],
            "funded": False,
            "note": spec.get("cost_note", ""),
            "source": (spec.get("cost_source") or w._GRAD_SRC)[0],
            "source_url": (spec.get("cost_source") or w._GRAD_SRC)[1],
            "year": "2025-26",
        }
    if spec.get("funded"):
        return {"funded": True, "note": "funded doctorate", "source": "GSAS", "source_url": "https://gradstudies.artsci.washu.edu/funding/"}
    return {"funded": False, "note": spec.get("omit_tuition_reason", "omitted"), "source": "x", "source_url": "https://washu.edu"}


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    st = w._program_standard(spec)
    outcomes = dict(w._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = st
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": w._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": w._TRACKS_BY_SLUG.get(slug),
        "application_requirements": w._requirements_for(spec),
        "cost_data": _program_cost(spec),
        "outcomes_data": outcomes,
        "class_profile": None,
        "faculty_contacts": None,
        "external_reviews": w._REVIEWS_BY_SLUG.get(slug),
        "content_sources": w._program_content(spec["school"], spec["keywords"]),
        "who_its_for": spec["who_its_for"],
        "_standard": st,
    }


def test_every_program_is_gold_or_omitted():
    assert len(w.PROGRAMS) == 58
    for spec in w.PROGRAMS:
        om = w._program_standard(spec)["omitted"]
        for f in _missing("program", _program_snapshot(spec)):
            assert f in om, f"{spec['slug']} field {f} missing and not omitted"


def test_matcher_core_fields_present_on_every_program():
    for spec in w.PROGRAMS:
        assert spec["cip"], f"{spec['slug']} missing cip_code"
        assert spec["who_its_for"].strip(), f"{spec['slug']} missing who_its_for"
        assert spec["description"].strip(), f"{spec['slug']} empty description"


def test_no_duplicate_program_names():
    seen = set()
    for spec in w.PROGRAMS:
        key = (spec["program_name"], spec["degree_type"])
        assert key not in seen, f"duplicate program {key}"
        seen.add(key)


def test_whole_bachelor_tier_carries_published_tuition():
    for spec in w.PROGRAMS:
        if spec["degree_type"] == "bachelors":
            assert _program_cost(spec)["tuition_usd"] == w._UG_TUITION


def test_no_graduate_row_carries_the_undergraduate_sticker():
    for spec in w.PROGRAMS:
        if spec["degree_type"] == "bachelors":
            continue
        cost = _program_cost(spec)
        assert cost.get("tuition_usd") != w._UG_TUITION, (
            f"{spec['slug']} carries the undergraduate sticker"
        )


def test_anti_stub_gate_is_gold_clean():
    progs = [{"program_name": p["program_name"], "description": p["description"]} for p in w.PROGRAMS]
    assert analyze(progs).is_clean
    assert not machine_artifacts(progs)
    assert not scrape_debris(progs)
    assert not template_slot_artifacts(progs)
    assert not frame_stripped_shared_body(progs)
    assert not frame_stripped_shared_body(progs, abs_chars=150)


def test_masters_tuition_fully_covered():
    """REPAIR_BACKLOG entry #1: the master's tier carries the published per-program annual
    rate on EVERY row — the two Olin specialized master's (MS Finance, MS Business Analytics)
    are now filled from their Olin Cost-Aid-Scholarships pages, closing the last null."""
    cov = defaultdict(lambda: [0, 0])
    for spec in w.PROGRAMS:
        dt = spec["degree_type"]
        cost = _program_cost(spec)
        cov[dt][1] += 1
        if cost.get("tuition_usd") is not None:
            cov[dt][0] += 1
    # Bachelor's tier is the institution-published sticker → 100%.
    assert cov["bachelors"][0] == cov["bachelors"][1]
    # Master's tier: 100% carry the published per-program annual rate (no null, no estimate).
    assert cov["masters"][0] == cov["masters"][1], f"masters tuition under-covered: {cov['masters']}"
    # The professional tier carries the published J.D. / M.D. rates.
    assert cov["professional"][0] == cov["professional"][1]
    # The two Olin specialized master's now carry a real per-program rate and are NOT omitted.
    for slug in _OLIN_FILLED:
        spec = next(s for s in w.PROGRAMS if s["slug"] == slug)
        cost = _program_cost(spec)
        assert cost.get("tuition_usd") is not None, f"{slug} should carry a published rate"
        assert cost["tuition_usd"] != w._UG_TUITION
        assert "cost_data.tuition_usd" not in w._program_standard(spec)["omitted"]
