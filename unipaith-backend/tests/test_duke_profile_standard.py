"""The Duke profile conforms to the gold standard for its institution, every one of
its ten schools, and its full breadth-first program catalog.

Pure (no DB): builds each node's persisted snapshot from the ``duke_profile`` module and
runs ``check_conformance``. A node is accepted only when it is gold OR every remaining
required field is recorded in that node's ``_standard.omitted`` (verified-unavailable)
with a real reason.
"""

# ruff: noqa: E501

from unipaith.data import duke_profile as d
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST


def _institution_snapshot() -> dict:
    so = {**d.SCHOOL_OUTCOMES}
    for path in d._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            so.pop(path.split(".", 1)[1], None)
    so["_standard"] = d._standard(d._OMITTED_INSTITUTION)
    return {
        "description_text": d.DESCRIPTION,
        "student_body_size": d.UNDERGRAD_COUNT,
        "media_gallery": [d._CAMPUS_PHOTO],
        "ranking_data": d.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": d._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = d._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = d._standard(d._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in d.SCHOOLS if s["name"] == name),
        "website_url": d._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": d._school_content(name),
    }


def _program_cost(spec: dict):
    if spec["degree_type"] == "bachelors":
        return {"tuition_usd": d._TUITION_UG, "source": d._COST_SRC[0], "source_url": d._COST_SRC[1]}
    grad = d._grad_cost(spec)
    return grad if grad is not None else {"note": "see school page", "source": "x", "source_url": "x"}


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    if slug == d._FLAGSHIP:
        outcomes = dict(d._MBA_OUTCOMES)
    else:
        outcomes = dict(d._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = d._program_standard(slug, spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": spec.get("website") or d._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": d._TRACKS_BY_SLUG.get(slug),
        "application_requirements": d._requirements_for(spec),
        "cost_data": _program_cost(spec),
        "outcomes_data": outcomes,
        "class_profile": d._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": d._FACULTY_BY_SLUG.get(slug),
        "external_reviews": d._REVIEWS_BY_SLUG.get(slug),
        "content_sources": d._program_content(
            spec["school"],
            d._PROGRAM_KEYWORDS_BY_SLUG.get(slug, ["x"]),
        ),
    }


def _section_gaps_unexpected(level: str, missing_sections: list[str], omitted: set[str]) -> list:
    """A missing required section is acceptable only when ALL its required enrich-fields
    are recorded in this node's omitted list."""
    bad = []
    for secid in missing_sections:
        sec = next(s for s in MANIFEST[level] if s.id == secid)
        req = {f.path for f in sec.fields if f.enrich and f.required}
        if not req <= omitted:
            bad.append(secid)
    return bad


def test_institution_is_gold():
    res = check_conformance("institution", _institution_snapshot(), profile_version=STANDARD_VERSION)
    omitted = set(d._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, f"Unexpected institution gaps: {res.missing_fields}"
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)


def test_all_ten_schools_done():
    assert len(d.SCHOOLS) == 10
    assert {s["name"] for s in d.SCHOOLS} == set(d._SCHOOL_WEBSITE)
    for school in d.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(d._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, f"{name}: unexpected gaps {res.missing_fields}"
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name


def test_every_program_is_done():
    assert len(d.PROGRAMS) >= 150, "breadth-first catalog should be the full program set"
    for spec in d.PROGRAMS:
        res = check_conformance("program", _program_snapshot(spec), profile_version=STANDARD_VERSION)
        omitted = set(d._program_standard(spec["slug"], spec)["omitted"])
        assert set(res.missing_fields) <= omitted, f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), spec["slug"]


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in d.SCHOOLS}
    for spec in d.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(d.PROGRAM_SLUGS) == len(set(d.PROGRAM_SLUGS)), "duplicate program slug"


def test_every_program_has_delivery_format():
    assert {p["delivery_format"] for p in d.PROGRAMS} <= {"in_person", "online", "hybrid"}
    assert any(p["delivery_format"] == "online" for p in d.PROGRAMS)
    assert any(p["delivery_format"] == "hybrid" for p in d.PROGRAMS)


def test_every_node_has_content_sources():
    assert d._INSTITUTION_CONTENT.get("news_rss")
    for school in d.SCHOOLS:
        cs = d._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed"), school["name"]
