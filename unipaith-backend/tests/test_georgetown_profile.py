"""The Georgetown profile conforms to the gold standard for its institution, all ten of its
degree-granting schools, and its full 190-program catalog.

Pure (no DB): builds each node's persisted snapshot from the ``georgetown_profile`` module and
runs ``check_conformance``. A node is accepted only when it is gold OR every remaining required
field is recorded in that node's ``_standard.omitted`` (verified-unavailable) with a real
reason. Also guards the matcher-side invariants: cip_code + who_its_for on every program, the
whole bachelor's tier carries the published tuition sticker, no graduate row carries the
undergraduate sticker, descriptions are non-empty, and the anti-stub gate is clean.
"""

# ruff: noqa: E501

from collections import defaultdict

from unipaith.data import georgetown_profile as g
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.anti_stub import (
    analyze,
    frame_stripped_shared_body,
    machine_artifacts,
    scrape_debris,
    template_slot_artifacts,
)

# A verified seed campus photo (apply() prepends the seed gallery's lead photo to
# media_gallery; the seed JSONB carries the 4-photo verified gallery).
_LEAD_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/"
    "Aerial_view_of_Georgetown_University.jpg/1920px-Aerial_view_of_Georgetown_University.jpg"
)


def _missing(level: str, snap: dict) -> list[str]:
    r = check_conformance(level, snap, profile_version=STANDARD_VERSION)
    return list(getattr(r, "missing_fields", []))


def _institution_snapshot() -> dict:
    so = {**g.SCHOOL_OUTCOMES}
    so["_standard"] = g._standard(g._OMITTED_INSTITUTION)
    return {
        "description_text": g.DESCRIPTION,
        "student_body_size": g.UNDERGRAD_COUNT,
        "media_gallery": [_LEAD_PHOTO],
        "ranking_data": g.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": g._INSTITUTION_CONTENT,
        "_standard": g._standard(g._OMITTED_INSTITUTION),
    }


def _school_snapshot(name: str) -> dict:
    about = dict(g._ABOUT_DETAIL[name])
    about["_standard"] = g._standard(g._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in g.SCHOOLS if s["name"] == name),
        "website_url": g._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": g._school_content(name),
        "_standard": g._standard(),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    cost = g._bachelor_cost() if spec["degree_type"] == "bachelors" else g._grad_cost(slug, spec)
    st = g._program_standard(slug, spec)
    outcomes = dict(g._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = st
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": g._duration_for(spec),
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": g._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": g._TRACKS_BY_SLUG.get(slug),
        "application_requirements": g._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": g._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": g._FACULTY_BY_SLUG.get(slug),
        "external_reviews": g._REVIEWS_BY_SLUG.get(slug),
        "content_sources": g._program_content(spec["school"], spec["keywords"]),
        "_standard": st,
    }


def test_institution_is_gold_or_omitted():
    snap = _institution_snapshot()
    for f in _missing("institution", snap):
        assert f in g._OMITTED_INSTITUTION, f"institution field {f} missing and not omitted"


def test_every_school_is_gold_or_omitted():
    assert len(g.SCHOOLS) == 10
    for sc in g.SCHOOLS:
        om = g._ABOUT_OMITTED.get(sc["name"], [])
        for f in _missing("school", _school_snapshot(sc["name"])):
            assert f in om, f"school {sc['name']} field {f} missing and not omitted"


def test_every_program_is_gold_or_omitted():
    assert len(g.PROGRAMS) == 190
    for spec in g.PROGRAMS:
        om = g._program_standard(spec["slug"], spec)["omitted"]
        for f in _missing("program", _program_snapshot(spec)):
            assert f in om, f"{spec['slug']} field {f} missing and not omitted"


def test_matcher_core_fields_present_on_every_program():
    for spec in g.PROGRAMS:
        assert g._CIP_BY_SLUG.get(spec["slug"]), f"{spec['slug']} missing cip_code"
        assert g._WHO_BY_SLUG.get(spec["slug"]), f"{spec['slug']} missing who_its_for"
        assert spec["description"].strip(), f"{spec['slug']} empty description"


def test_no_duplicate_program_names():
    seen = set()
    for spec in g.PROGRAMS:
        key = (spec["program_name"], spec["degree_type"])
        assert key not in seen, f"duplicate program {key}"
        seen.add(key)


def test_whole_bachelor_tier_carries_published_tuition():
    for spec in g.PROGRAMS:
        if spec["degree_type"] == "bachelors":
            assert g._bachelor_cost()["tuition_usd"] == g._TUITION_UG


def test_no_graduate_row_carries_the_undergraduate_sticker():
    for spec in g.PROGRAMS:
        if spec["degree_type"] == "bachelors":
            continue
        cost = g._grad_cost(spec["slug"], spec)
        assert cost.get("tuition_usd") != g._TUITION_UG, (
            f"{spec['slug']} carries the undergraduate sticker"
        )


def test_anti_stub_gate_is_gold_clean():
    progs = [{"program_name": p["program_name"], "description": p["description"]} for p in g.PROGRAMS]
    assert analyze(progs).is_clean
    assert not machine_artifacts(progs)
    assert not scrape_debris(progs)
    assert not template_slot_artifacts(progs)
    assert not frame_stripped_shared_body(progs)
    assert not frame_stripped_shared_body(progs, abs_chars=150)


def test_tuition_coverage_by_tier():
    cov = defaultdict(lambda: [0, 0])
    for spec in g.PROGRAMS:
        dt = spec["degree_type"]
        cost = g._bachelor_cost() if dt == "bachelors" else g._grad_cost(spec["slug"], spec)
        cov[dt][1] += 1
        if cost.get("tuition_usd") is not None:
            cov[dt][0] += 1
    # Bachelor's tier is the institution-published sticker → 100%.
    assert cov["bachelors"][0] == cov["bachelors"][1]
    # The professional tier carries the published JD / MD / MBA / LL.M. rates.
    assert cov["professional"][0] >= 10


def test_graduate_tuition_fills_present():
    """The verified master's/professional tuition fills land with their published values."""
    specs = {p["slug"]: p for p in g.PROGRAMS}
    expected = {
        "georgetown-english-ma": 79560,  # GSAS $2,652/credit x 30 credits
        "georgetown-spanish-linguistics-ms": 87516,  # GSAS $2,652/credit x 33 credits
        "georgetown-executive-dnp": 82740,  # Nursing@Georgetown $2,758/credit x 30 credits
        "georgetown-policy-leadership-empl": 82104,  # 6 cr @ $2,652 + 24 cr @ $2,758
    }
    for slug, amount in expected.items():
        cost = g._grad_cost(slug, specs[slug])
        assert cost.get("tuition_usd") == amount, f"{slug} tuition should be {amount}"
        assert "cost_data.tuition_usd" not in g._program_standard(slug, specs[slug])["omitted"]


def test_unpublished_graduate_tuition_is_omitted_with_reason():
    """Programs with no verifiable first-party tuition stay null AND recorded as omitted."""
    specs = {p["slug"]: p for p in g.PROGRAMS}
    for slug in (
        "georgetown-sjd",
        "georgetown-nurse-anesthesia-dnap",
        "georgetown-nursing-dnp",
        "georgetown-nursing-ms",
        "georgetown-clinical-quality-safety-leadership-ms",
    ):
        cost = g._grad_cost(slug, specs[slug])
        assert cost.get("tuition_usd") is None, f"{slug} should be omitted, not filled"
        assert "cost_data.tuition_usd" in g._program_standard(slug, specs[slug])["omitted"]
        assert cost["note"], f"{slug} omission must carry a reason"
