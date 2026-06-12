"""The UC Berkeley profile conforms to the gold standard across its whole tree.

Pure (no DB): builds each node's persisted snapshot from ``berkeley_profile`` and runs
``check_conformance``. A node passes when it is gold OR every remaining required gap is
recorded in that node's ``_standard.omitted``.
"""

from unipaith.data import berkeley_profile as b
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "berkeley-eecs-bs"


def _required_fields_of_section(level: str, section_id: str) -> set[str]:
    sec = next(s for s in MANIFEST[level] if s.id == section_id)
    return {f.path for f in sec.fields if f.required and f.enrich}


def _gaps_are_all_omitted(level: str, res, omitted: set[str]) -> tuple[bool, set]:
    bad = set(res.missing_fields) - omitted
    for sec_id in res.missing_sections:
        if not _required_fields_of_section(level, sec_id) <= omitted:
            bad |= {f"section:{sec_id}"}
    return (not bad), bad


def _institution_snapshot() -> dict:
    school_outcomes = {**b.SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = b._standard(b._OMITTED_INSTITUTION)
    return {
        "description_text": b.DESCRIPTION,
        "student_body_size": b.UNDERGRAD_COUNT,
        "media_gallery": [b._CAMPUS_PHOTO],
        "ranking_data": b.RANKING_DATA,
        "school_outcomes": school_outcomes,
        "content_sources": b._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = b._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = b._standard(b._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in b.SCHOOLS if s["name"] == name),
        "website_url": b._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": b._school_content(name),
    }


def _program_snapshot(slug: str) -> dict:
    spec = b._SPEC_BY_SLUG[slug]
    if spec["degree_type"] == "bachelors":
        cost = {
            "tuition_usd": b._TUITION_IN_STATE,
            "source": "x",
            "source_url": "x",
        }
    else:
        cost = {
            "funded": spec["degree_type"] == "phd",
            "note": "see program website",
            "source": "x",
            "source_url": "x",
        }
    fos = b._FOS_OUTCOMES.get(slug)
    if fos is not None:
        salary, cip = fos
        outcomes = {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "conditions": b._FOS_CONDITIONS,
            "source": "College Scorecard",
            "source_url": "x",
        }
    else:
        outcomes = dict(b._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = b._program_standard(slug, spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": b._WEBSITE_BY_SLUG.get(slug) or b._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": b._HL_BY_SLUG.get(slug) or b._HL_BASELINE,
        "who_its_for": b._WHO_BY_SLUG.get(slug) or b._WHO_BASELINE,
        "tracks": b._TRACKS_BY_SLUG.get(slug),
        "application_requirements": b._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": b._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": b._FACULTY_BY_SLUG.get(slug),
        "external_reviews": b._REVIEWS_BY_SLUG.get(slug),
        "content_sources": (
            b._EECS_CONTENT if slug == _FLAGSHIP else b._program_content(spec)
        ),
    }


def test_berkeley_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    omitted = set(b._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    ok, bad = _gaps_are_all_omitted("institution", res, omitted)
    assert ok, f"Unexpected institution section gaps: {bad}"


def test_every_school_is_gold_except_recorded_omissions():
    assert len(b.SCHOOLS) == 12
    for school in b.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(b._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        ok, bad = _gaps_are_all_omitted("school", res, allowed)
        assert ok, f"{name} unexpected section gaps: {bad}"


def test_every_program_is_gold_except_recorded_omissions():
    assert len(b.PROGRAMS) >= 250, "full Scorecard catalog breadth (UNITID 110635)"
    for spec in b.PROGRAMS:
        slug = spec["slug"]
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        allowed = set(b._program_standard(slug, spec)["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        ok, bad = _gaps_are_all_omitted("program", res, allowed)
        assert ok, f"{slug} unexpected section gaps: {bad}"


def test_every_node_has_content_sources():
    assert b._INSTITUTION_CONTENT.get("news_rss")
    assert b._INSTITUTION_CONTENT.get("events_feed")
    for school in b.SCHOOLS:
        cs = b._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), school["name"]
    for spec in b.PROGRAMS:
        cs = b._EECS_CONTENT if spec["slug"] == _FLAGSHIP else b._program_content(spec)
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), spec["slug"]


def test_eecs_flagship_is_deeply_enriched():
    assert _FLAGSHIP in b._TRACKS_BY_SLUG
    assert _FLAGSHIP in b._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in b._FACULTY_BY_SLUG
    assert _FLAGSHIP in b._REVIEWS_BY_SLUG


def test_coverable_programs_have_external_reviews():
    """Coverable Berkeley programs must carry aggregated external_reviews."""
    coverable = [
        _FLAGSHIP,
        "berkeley-computer-science-bs",
        "berkeley-data-science-bs",
        "berkeley-economics-bs",
        "berkeley-mechanical-engineering-bs",
        "berkeley-chemical-engineering-bs",
        "berkeley-business-administration-bs",
        "berkeley-business-administration-management-and-operations-prof",
        "berkeley-law-prof",
        "berkeley-public-policy-analysis-prof",
        "berkeley-public-health-prof",
        "berkeley-architecture-prof",
    ]
    for slug in coverable:
        assert slug in b._REVIEWS_BY_SLUG, slug
        assert b._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(b._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in b.SCHOOLS}
    for spec in b.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(b.PROGRAM_SLUGS) == len(set(b.PROGRAM_SLUGS)), "duplicate program slug"
