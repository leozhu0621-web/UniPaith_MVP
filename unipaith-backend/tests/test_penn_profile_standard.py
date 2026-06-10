"""The University of Pennsylvania profile (the completed tree) conforms to the gold
standard across every node it models — the institution, twelve schools, and their
twenty-four programs — mirroring the MIT/Sloan/MBAn and the Columbia/Yale reference
certifications.

Pure (no DB): builds each node's persisted snapshot from the penn_profile module and runs
``check_conformance``. The only gaps permitted are the fields each node honestly records in
its ``_standard.omitted`` lists. Penn carries one deeply-enriched flagship (the Wharton
MBA); every one of the twelve schools owns at least one fully enriched program.
"""

from unipaith.data import penn_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

_FLAGSHIP = "penn-wharton-mba"
# The six graduate/professional flagship programs added by the final resume run.
_RESUME_PROGRAMS = {
    "penn-dmd",
    "penn-vmd",
    "penn-march",
    "penn-msw",
    "penn-gse-higher-education-msed",
    "penn-communication-phd",
}


def _institution_snapshot() -> dict:
    school_outcomes = {**p.SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = p._standard(p._OMITTED_INSTITUTION)
    return {
        "description_text": p.DESCRIPTION,
        "student_body_size": p.UNDERGRAD_COUNT,
        "media_gallery": [p._CAMPUS_PHOTO],
        "ranking_data": p.RANKING_DATA,
        "school_outcomes": school_outcomes,
        "content_sources": p._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = p._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = p._standard(p._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in p.SCHOOLS if s["name"] == name),
        "website_url": p._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": None,
    }


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = next(pr for pr in p.PROGRAMS if pr["slug"] == slug)
    is_undergrad = spec["degree_type"] == "bachelors"
    if slug == _FLAGSHIP:
        outcomes = dict(p._WHARTON_MBA_OUTCOMES)
    else:
        fos = p._FOS_OUTCOMES.get(slug)
        if fos is not None:
            outcomes = {
                "median_salary": fos[0],
                "scope": "program",
                "cip": fos[1],
                "conditions": p._FOS_CONDITIONS,
                "source": "x",
                "source_url": "x",
            }
        else:
            outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug)
    cost_override = p._COST_BY_SLUG.get(slug)
    if cost_override is not None:
        cost = dict(cost_override)
    elif is_undergrad:
        cost = {"tuition_usd": p._TUITION_UG, "source": "x"}
    else:
        cost = None
    return {
        "program_name": p._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": p._WEBSITE_BY_SLUG.get(slug),
        "highlights": p._HL_BY_SLUG.get(slug) or p._HL_BASELINE,
        "who_its_for": p._WHO_BY_SLUG.get(slug) or p._WHO_BASELINE,
        "tracks": p._TRACKS_BY_SLUG.get(slug),
        "application_requirements": p._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": p._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": p._FACULTY_BY_SLUG.get(slug),
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug),
        "content_sources": p._WHARTON_MBA_CONTENT if slug == _FLAGSHIP else None,
    }


def test_penn_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(p._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections


def test_every_school_is_gold_except_recorded_omissions():
    assert len(p.SCHOOLS) == 12
    for school in p.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(p._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, f"{name} missing sections: {res.missing_sections}"


def test_wharton_mba_flagship_is_deeply_enriched():
    # The flagship carries curriculum, class profile, faculty, reviews and its own feed —
    # so the only recorded omissions are the college-wide employment fields.
    assert _FLAGSHIP in p._TRACKS_BY_SLUG
    assert _FLAGSHIP in p._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in p._FACULTY_BY_SLUG
    assert _FLAGSHIP in p._REVIEWS_BY_SLUG
    assert p._program_standard(_FLAGSHIP)["omitted"] == []


def test_every_program_is_gold_except_recorded_omissions():
    omittable_sections = {"tracks", "costs", "insights", "feeds"}
    assert len(p.PROGRAMS) == 24
    for spec in p.PROGRAMS:
        slug = spec["slug"]
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        allowed = set(p._program_standard(slug)["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        assert set(res.missing_sections) <= omittable_sections, (
            f"{slug} unexpected section gaps: {res.missing_sections}"
        )


def test_resume_programs_carry_verified_cost_and_admissions():
    # Each newly added graduate/professional flagship ships a first-party cost of
    # attendance and an admissions requirement set with a cited source.
    for slug in _RESUME_PROGRAMS:
        cost = p._COST_BY_SLUG.get(slug)
        assert cost and cost.get("source_url"), f"{slug} missing cited cost"
        assert cost.get("tuition_usd") is not None, f"{slug} missing tuition"
        spec = next(pr for pr in p.PROGRAMS if pr["slug"] == slug)
        req = p._requirements_for(spec)
        assert req.get("materials") and req.get("source_url"), f"{slug} missing admissions"


def test_every_school_owns_at_least_one_program():
    by_school = {s["name"]: 0 for s in p.SCHOOLS}
    for spec in p.PROGRAMS:
        assert spec["school"] in by_school, f"{spec['slug']} maps to unknown unit"
        by_school[spec["school"]] += 1
    empty = [name for name, n in by_school.items() if n == 0]
    assert not empty, f"schools with no program: {empty}"


def test_every_program_maps_to_a_real_unit_with_unique_slug():
    unit_names = {s["name"] for s in p.SCHOOLS}
    for spec in p.PROGRAMS:
        assert spec["school"] in unit_names, f"{spec['slug']} maps to unknown unit"
    assert len(p.PROGRAM_SLUGS) == len(set(p.PROGRAM_SLUGS)), "duplicate program slug"


def test_all_units_have_about_detail():
    assert {s["name"] for s in p.SCHOOLS} == set(p._SCHOOL_WEBSITE)
    for school in p.SCHOOLS:
        assert p._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"
