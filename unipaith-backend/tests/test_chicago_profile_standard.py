"""The University of Chicago profile conforms to the gold standard across its whole tree.

Pure (no DB): builds each node's persisted snapshot from ``chicago_profile`` and runs
``check_conformance``. A node passes when it is gold OR every remaining required gap is
recorded in that node's ``_standard.omitted``.
"""

from unipaith.data import chicago_profile as c
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "uchicago-mba"


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
    school_outcomes = {**c.SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = c._standard(c._OMITTED_INSTITUTION)
    return {
        "description_text": c.DESCRIPTION,
        "student_body_size": c.UNDERGRAD_COUNT,
        "media_gallery": [c._CAMPUS_PHOTO],
        "ranking_data": c.RANKING_DATA,
        "school_outcomes": school_outcomes,
        "content_sources": c._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = c._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = c._standard(c._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in c.SCHOOLS if s["name"] == name),
        "website_url": c._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": c._school_content(name),
    }


def _program_snapshot(slug: str) -> dict:
    spec = c._SPEC_BY_SLUG[slug]
    is_undergrad = spec["degree_type"] == "bachelors"
    if slug == _FLAGSHIP:
        outcomes = dict(c._MBA_OUTCOMES)
    else:
        fos = c._FOS_OUTCOMES.get(slug)
        if fos is not None:
            outcomes = {
                "median_salary": fos[0],
                "scope": "program",
                "cip": fos[1],
                "conditions": c._FOS_CONDITIONS_BY_SLUG.get(slug, c._FOS_CONDITIONS),
                "source": "x",
                "source_url": "x",
            }
        else:
            outcomes = dict(c._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = c._program_standard(slug, spec)
    cost_override = c._COST_BY_SLUG.get(slug)
    if cost_override is not None:
        cost = dict(cost_override)
    elif is_undergrad:
        cost = {"tuition_usd": c._TUITION_UG, "source": "x"}
    elif slug in c._COST_OMITTED_SLUGS:
        cost = dict(c._COST_OMITTED_RECORD)
    elif spec["degree_type"] in ("masters", "professional", "phd", "certificate"):
        cost = {
            "funded": spec["degree_type"] == "phd",
            "note": "see program website",
            "source": "x",
        }
    else:
        cost = None
    return {
        "program_name": c._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": c._WEBSITE_BY_SLUG.get(slug) or c._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": c._HL_BY_SLUG.get(slug) or (
            c._HL_BASELINE if is_undergrad else c._HL_GRAD_BASELINE
        ),
        "who_its_for": c._WHO_BY_SLUG.get(slug) or (
            c._WHO_BASELINE if is_undergrad else c._WHO_GRAD_BASELINE
        ),
        "tracks": c._TRACKS_BY_SLUG.get(slug),
        "application_requirements": c._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": c._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": c._FACULTY_BY_SLUG.get(slug),
        "external_reviews": c._REVIEWS_BY_SLUG.get(slug),
        "content_sources": (
            c._BOOTH_CONTENT if slug == _FLAGSHIP else c._program_content(spec)
        ),
    }


def test_chicago_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    omitted = set(c._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    ok, bad = _gaps_are_all_omitted("institution", res, omitted)
    assert ok, f"Unexpected institution section gaps: {bad}"


def test_every_school_is_gold_except_recorded_omissions():
    assert len(c.SCHOOLS) == 11
    for school in c.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(c._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        ok, bad = _gaps_are_all_omitted("school", res, allowed)
        assert ok, f"{name} unexpected section gaps: {bad}"


def test_every_program_is_gold_except_recorded_omissions():
    assert len(c.PROGRAMS) >= 100, "full IPEDS catalog breadth (UNITID 144050)"
    for spec in c.PROGRAMS:
        slug = spec["slug"]
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        allowed = set(c._program_standard(slug, spec)["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        ok, bad = _gaps_are_all_omitted("program", res, allowed)
        assert ok, f"{slug} unexpected section gaps: {bad}"


def test_every_node_has_content_sources():
    assert c._INSTITUTION_CONTENT.get("news_rss")
    assert c._INSTITUTION_CONTENT.get("events_feed")
    for school in c.SCHOOLS:
        cs = c._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), school["name"]
    for spec in c.PROGRAMS:
        cs = c._BOOTH_CONTENT if spec["slug"] == _FLAGSHIP else c._program_content(spec)
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), spec["slug"]


def test_booth_mba_flagship_is_deeply_enriched():
    assert _FLAGSHIP in c._TRACKS_BY_SLUG
    assert _FLAGSHIP in c._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in c._REVIEWS_BY_SLUG
    assert set(c._program_standard(_FLAGSHIP)["omitted"]) == {
        "outcomes_data.employment_rate",
        "faculty_contacts.lead",
    }


def test_coverable_programs_have_external_reviews():
    """Coverable programs (MBA, JD, MD, MPP, flagship CS) must carry reviews."""
    coverable = [
        _FLAGSHIP,
        "uchicago-computer-science-bs",
        "uchicago-jd",
        "uchicago-md",
        "uchicago-mpp",
    ]
    for slug in coverable:
        assert slug in c._REVIEWS_BY_SLUG, slug
        assert c._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(c._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_institution_has_media_credit():
    assert c.SCHOOL_OUTCOMES.get("media_credit"), "campus photo must carry attribution"


def test_description_leads_with_research_university():
    assert c.DESCRIPTION.startswith(
        "University of Chicago is a private research university in Chicago, IL"
    )


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in c.SCHOOLS}
    for spec in c.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(c.PROGRAM_SLUGS) == len(set(c.PROGRAM_SLUGS)), "duplicate program slug"
