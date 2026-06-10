"""The Caltech profile conforms to the gold standard for its certified nodes —
the institution and a representative division (Biology and Biological Engineering)
— mirroring the MIT/Sloan/MBAn and Stanford certifications.

Pure (no DB): builds each node's persisted snapshot from the caltech_profile module
and runs ``check_conformance``. The only gaps permitted at any level are the fields
the module honestly records in its ``_standard.omitted`` lists (Caltech publishes no
per-program employment report and withheld employer industries, and only the Biology
division publishes a first-party founding year).
"""

from unipaith.data import caltech_profile as ct
from unipaith.profile_standard import STANDARD_VERSION, check_conformance


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = next(p for p in ct.PROGRAMS if p["slug"] == slug)
    fos = ct._FOS_OUTCOMES.get(slug)
    if fos is not None:
        salary, cip = fos
        outcomes = {"median_salary": salary, "scope": "program", "cip": cip, "source": "x"}
    else:
        outcomes = dict(ct._OUTCOMES_INSTITUTION)
    if spec["degree_type"] == "phd":
        cost = {"tuition_usd": 0, "source": "x"}
    else:
        cost = {"tuition_usd": ct._TUITION_UNDERGRAD, "source": "x"}
    req = ct._REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else ct._REQ_GRAD
    website = ct._WEBSITE_BY_SLUG.get(slug) or (
        ct._GRAD_OPTIONS_URL
        if spec["degree_type"] == "phd"
        else ct._SCHOOL_WEBSITE.get(spec["school"])
    )
    return {
        "program_name": ct._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": website,
        "highlights": ct._HL_BY_SLUG.get(slug) or ct._HL_BY_TYPE.get(spec["degree_type"]),
        "who_its_for": ct._WHO_BY_SLUG.get(slug) or ct._WHO_BY_TYPE.get(spec["degree_type"]),
        "tracks": ct._TRACKS_BY_SLUG.get(slug),
        "application_requirements": req,
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": ct._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": ct._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": ct._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": ct._CS_CONTENT if slug == "caltech-cs-bs" else None,
    }


def _school_snapshot(name: str) -> dict:
    return {
        "name": name,
        "description_text": next(s["description"] for s in ct.SCHOOLS if s["name"] == name),
        "website_url": ct._SCHOOL_WEBSITE.get(name),
        "about_detail": ct._ABOUT_DETAIL.get(name),
        "content_sources": None,
    }


def _institution_snapshot() -> dict:
    return {
        "description_text": ct.DESCRIPTION,
        "student_body_size": ct.UNDERGRAD_COUNT,
        "media_gallery": [ct._CAMPUS_PHOTO],
        "ranking_data": ct.RANKING_DATA,
        "school_outcomes": ct.SCHOOL_OUTCOMES,
        "content_sources": ct._INSTITUTION_CONTENT,
    }


def test_caltech_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    # The only permitted gaps are the fields the module honestly omits.
    assert set(res.missing_fields) <= set(ct._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections
    assert "school_outcomes.top_employer_industries" in ct._OMITTED_INSTITUTION


def test_caltech_biology_division_is_conformant():
    res = check_conformance("school", _school_snapshot(ct._BBE), profile_version=STANDARD_VERSION)
    assert res.conformant, f"BBE gaps: {res.missing_fields} {res.missing_sections}"


def test_caltech_cs_flagship_has_full_insights_and_tracks():
    # Caltech publishes no per-program employment report, so the flagship cannot be
    # strictly conformant on the outcomes section — but it must carry tracks, class
    # profile, faculty, and aggregated reviews, with its outcome gaps honestly
    # recorded in _standard.omitted.
    snap = _program_snapshot("caltech-cs-bs")
    res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
    assert snap["tracks"] and snap["tracks"]["items"]
    assert snap["class_profile"].get("cohort_size")
    assert snap["faculty_contacts"].get("lead")
    assert snap["external_reviews"].get("summary")
    std = ct._program_standard("caltech-cs-bs", "bachelors", True)
    for path in res.missing_fields:
        assert path in std["omitted"], f"Unrecorded flagship gap: {path}"


def test_all_six_divisions_have_about_detail():
    assert {s["name"] for s in ct.SCHOOLS} == set(ct._SCHOOL_WEBSITE)
    assert len(ct.SCHOOLS) == 6
    for school in ct.SCHOOLS:
        about = ct._ABOUT_DETAIL.get(school["name"])
        assert about and about.get("leadership"), f"{school['name']} missing about_detail"


def test_every_program_maps_to_a_real_division():
    school_names = {s["name"] for s in ct.SCHOOLS}
    for spec in ct.PROGRAMS:
        assert spec["school"] in school_names, f"{spec['slug']} maps to unknown division"
    assert len(ct.PROGRAM_SLUGS) == len(set(ct.PROGRAM_SLUGS)), "duplicate program slug"
