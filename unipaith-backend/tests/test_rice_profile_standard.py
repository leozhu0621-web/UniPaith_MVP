"""The Rice profile conforms to the gold standard for its institution, every one of its
eight schools, and its full breadth-first program catalog.

Pure (no DB): builds each node's persisted snapshot from the ``rice_profile`` module and
runs ``check_conformance``. A node is accepted only when it is gold OR every remaining
required field is recorded in that node's ``_standard.omitted`` (verified-unavailable) with
a real reason.
"""

# ruff: noqa: E501

from unipaith.data import rice_profile as r
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = r._FLAGSHIP


def _institution_snapshot() -> dict:
    so = {**r.SCHOOL_OUTCOMES}
    for path in r._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            so.pop(path.split(".", 1)[1], None)
    so["_standard"] = r._standard(r._OMITTED_INSTITUTION)
    return {
        "description_text": r.DESCRIPTION,
        "student_body_size": r.UNDERGRAD_COUNT,
        "media_gallery": [r._CAMPUS_PHOTO],
        "ranking_data": r.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": r._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = r._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = r._standard(r._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in r.SCHOOLS if s["name"] == name),
        "website_url": r._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": r._school_content(name),
    }


def _program_cost(spec: dict):
    slug = spec["slug"]
    override = r._COST_BY_SLUG.get(slug)
    if override is not None:
        return override
    if spec["degree_type"] == "bachelors":
        return {"tuition_usd": r._TUITION_UG, "source": r._COST_SRC[0], "source_url": r._COST_SRC[1]}
    grad = r._grad_cost(spec)
    return grad if grad is not None else {"note": "see school page", "source": "x", "source_url": "x"}


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    if slug == _FLAGSHIP:
        outcomes = dict(r._MBA_OUTCOMES)
    else:
        outcomes = dict(r._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = r._program_standard(slug, spec)
    _kw = r._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
        r._SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
    )
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": spec.get("website") or r._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": r._TRACKS_BY_SLUG.get(slug),
        "application_requirements": r._requirements_for(spec),
        "cost_data": _program_cost(spec),
        "outcomes_data": outcomes,
        "class_profile": r._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": r._FACULTY_BY_SLUG.get(slug),
        "external_reviews": r._REVIEWS_BY_SLUG.get(slug),
        "content_sources": r._program_content(spec["school"], _kw),
    }


def _section_gaps_unexpected(level: str, missing_sections: list[str], omitted: set[str]) -> list:
    """A missing required section is acceptable only when ALL its required enrich-fields are
    recorded in this node's omitted list."""
    bad = []
    for secid in missing_sections:
        sec = next(s for s in MANIFEST[level] if s.id == secid)
        req = {f.path for f in sec.fields if f.enrich and f.required}
        if not req <= omitted:
            bad.append(secid)
    return bad


def test_institution_is_gold():
    res = check_conformance("institution", _institution_snapshot(), profile_version=STANDARD_VERSION)
    omitted = set(r._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, f"Unexpected institution gaps: {res.missing_fields}"
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)
    assert r.SCHOOL_OUTCOMES.get("media_credit")


def test_all_eight_schools_done():
    assert len(r.SCHOOLS) == 8
    assert {s["name"] for s in r.SCHOOLS} == set(r._SCHOOL_WEBSITE)
    for school in r.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(r._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, f"{name}: unexpected gaps {res.missing_fields}"
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name


def test_rice_mba_flagship_is_deeply_enriched():
    assert _FLAGSHIP in r._TRACKS_BY_SLUG
    assert _FLAGSHIP in r._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in r._REVIEWS_BY_SLUG
    assert r._program_standard(_FLAGSHIP, r._SPEC_BY_SLUG[_FLAGSHIP])["omitted"] == []


def test_coverable_programs_have_external_reviews():
    coverable = [
        _FLAGSHIP,
        "rice-computer-science-ug",
        "rice-master-of-computer-science-mcs-rice-online-prof",
        "rice-master-of-data-science-mds-rice-online-prof",
        "rice-master-of-architecture-march-option-1-professional-prof",
        "rice-economics-ug",
    ]
    for slug in coverable:
        assert slug in r._REVIEWS_BY_SLUG, slug
        assert r._REVIEWS_BY_SLUG[slug].get("summary"), slug


def test_every_program_is_done():
    assert len(r.PROGRAMS) >= 150, "breadth-first catalog should be the full program set"
    for spec in r.PROGRAMS:
        res = check_conformance("program", _program_snapshot(spec), profile_version=STANDARD_VERSION)
        omitted = set(r._program_standard(spec["slug"], spec)["omitted"])
        assert set(res.missing_fields) <= omitted, f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), spec["slug"]


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in r.SCHOOLS}
    for spec in r.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(r.PROGRAM_SLUGS) == len(set(r.PROGRAM_SLUGS)), "duplicate program slug"


def test_every_program_has_delivery_format():
    assert {p["delivery_format"] for p in r.PROGRAMS} <= {"in_person", "online", "hybrid"}
    assert any(p["delivery_format"] == "online" for p in r.PROGRAMS)
    assert any(p["delivery_format"] == "hybrid" for p in r.PROGRAMS)


def test_every_node_has_content_sources():
    assert r._INSTITUTION_CONTENT.get("news_rss")
    for school in r.SCHOOLS:
        cs = r._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed"), school["name"]
