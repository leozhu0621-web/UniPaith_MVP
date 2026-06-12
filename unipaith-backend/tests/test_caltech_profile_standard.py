"""The Caltech profile conforms to the gold standard across its whole tree — the
institution, six academic divisions, and the full published degree catalog —
mirroring the MIT/Sloan/MBAn and Berkeley reference certifications.

Pure (no DB): builds each node's persisted snapshot from the caltech_profile module
and runs ``check_conformance``. The only gaps permitted are the fields each node
honestly records in its ``_standard.omitted`` lists.
"""

from unipaith.data import caltech_profile as c
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "caltech-cs-bs"
_OMITTABLE_SECTIONS = {"tracks", "insights"}


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
    for path in c._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            school_outcomes.pop(path.split(".", 1)[1], None)
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
    fos = c._FOS_OUTCOMES.get(slug)
    if fos is not None:
        salary, cip = fos
        outcomes = {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "source": "College Scorecard",
            "source_url": "x",
        }
        has_program_outcomes = True
    else:
        outcomes = dict(c._OUTCOMES_INSTITUTION)
        has_program_outcomes = False
    outcomes["_standard"] = c._program_standard(
        slug, spec, has_program_outcomes=has_program_outcomes
    )
    if spec["degree_type"] == "phd":
        cost = {
            "tuition_usd": 0,
            "funded": True,
            "source": "Caltech Graduate Studies Office",
            "source_url": "x",
        }
    else:
        cost = {
            "tuition_usd": c._TUITION_UNDERGRAD,
            "source": "College Scorecard",
            "source_url": "x",
        }
    req = c._REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else c._REQ_GRAD
    return {
        "program_name": c._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": c._WEBSITE_BY_SLUG.get(slug) or c._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": c._HL_BY_SLUG.get(slug) or c._HL_BY_TYPE.get(spec["degree_type"]),
        "who_its_for": c._WHO_BY_SLUG.get(slug) or c._WHO_BY_TYPE.get(spec["degree_type"]),
        "tracks": c._TRACKS_BY_SLUG.get(slug),
        "application_requirements": req,
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": c._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": c._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": c._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": (
            c._CS_CONTENT if slug == _FLAGSHIP else c._program_content(spec)
        ),
    }


def test_caltech_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    omitted = set(c._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    ok, bad = _gaps_are_all_omitted("institution", res, omitted)
    assert ok, f"Unexpected institution section gaps: {bad}"
    assert c.SCHOOL_OUTCOMES.get("media_credit")
    assert "private research university" in c.DESCRIPTION.lower()


def test_every_division_is_gold_except_recorded_omissions():
    assert len(c.SCHOOLS) == 6
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
    assert len(c.PROGRAMS) >= 70, "full IPEDS/Scorecard catalog breadth (UNITID 110404)"
    for spec in c.PROGRAMS:
        slug = spec["slug"]
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        fos = c._FOS_OUTCOMES.get(slug)
        has_program_outcomes = fos is not None
        allowed = set(
            c._program_standard(slug, spec, has_program_outcomes=has_program_outcomes)["omitted"]
        )
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        assert set(res.missing_sections) <= _OMITTABLE_SECTIONS, (
            f"{slug} unexpected section gaps: {res.missing_sections}"
        )


def test_every_node_has_content_sources():
    assert c._INSTITUTION_CONTENT.get("news_rss")
    assert c._INSTITUTION_CONTENT.get("events_feed")
    for school in c.SCHOOLS:
        cs = c._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), school["name"]
    for spec in c.PROGRAMS:
        cs = c._CS_CONTENT if spec["slug"] == _FLAGSHIP else c._program_content(spec)
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), spec["slug"]


def test_cs_flagship_is_deeply_enriched():
    assert _FLAGSHIP in c._TRACKS_BY_SLUG
    assert _FLAGSHIP in c._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in c._FACULTY_BY_SLUG
    assert _FLAGSHIP in c._REVIEWS_BY_SLUG


def test_every_program_maps_to_a_real_division():
    names = {s["name"] for s in c.SCHOOLS}
    for spec in c.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} maps to unknown division"
    assert len(c.PROGRAM_SLUGS) == len(set(c.PROGRAM_SLUGS)), "duplicate program slug"
