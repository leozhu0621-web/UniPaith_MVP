"""The Harvard profile conforms to the gold standard for its certified trio — the
institution, Harvard Business School, and the flagship MBA program — mirroring the
MIT/Sloan/MBAn and Stanford reference certifications.

Pure (no DB): builds each node's persisted snapshot from the harvard_profile module
and runs ``check_conformance``. The only institution-level gap permitted is the field
Harvard does not cleanly publish and that the module honestly records in its
``_standard.omitted`` list.
"""

from unipaith.data import harvard_profile as h
from unipaith.profile_standard import STANDARD_VERSION, check_conformance


def _institution_snapshot() -> dict:
    school_outcomes = {**h.SCHOOL_OUTCOMES}
    for path in h._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            school_outcomes.pop(path.split(".", 1)[1], None)
    school_outcomes["_standard"] = h._standard(h._OMITTED_INSTITUTION)
    return {
        "description_text": h.DESCRIPTION,
        "student_body_size": h.UNDERGRAD_COUNT,
        "media_gallery": [h._CAMPUS_PHOTO],
        "ranking_data": h.RANKING_DATA,
        "school_outcomes": school_outcomes,
        "content_sources": h._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = h._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = h._standard(h._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in h.SCHOOLS if s["name"] == name),
        "website_url": h._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": h._HBS_CONTENT if name == h._HBS else None,
    }


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = next(p for p in h.PROGRAMS if p["slug"] == slug)
    out_override = h._OUTCOMES_BY_SLUG.get(slug)
    fos = h._FOS_OUTCOMES.get(slug)
    has_program_outcomes = False
    if out_override is not None:
        outcomes = dict(out_override)
        has_program_outcomes = True
    elif fos is not None:
        salary, debt, cip = fos
        outcomes = {"median_salary": salary, "scope": "program", "cip": cip, "source": "x"}
    elif spec["degree_type"] in ("bachelors", "masters", "phd"):
        outcomes = dict(h._OUTCOMES_INSTITUTION)
    else:
        outcomes = None
    if outcomes is not None:
        outcomes["_standard"] = h._program_standard(
            slug, spec["degree_type"], has_program_outcomes
        )
    return {
        "program_name": h._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": h._DESC_RICH_BY_SLUG.get(slug) or spec["description"],
        "website_url": h._WEBSITE_BY_SLUG.get(slug),
        "highlights": h._HL_BY_SLUG.get(slug) or h._HL_BY_TYPE.get(spec["degree_type"]),
        "who_its_for": h._WHO_BY_SLUG.get(slug) or h._WHO_BY_TYPE.get(spec["degree_type"]),
        "tracks": h._TRACKS_BY_SLUG.get(slug),
        "application_requirements": h._requirements_for(spec),
        "cost_data": {"tuition_usd": 78700, "source": "x"},
        "outcomes_data": outcomes,
        "class_profile": h._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": h._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": h._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": h._MBA_CONTENT if slug == "harvard-mba" else None,
    }


def test_harvard_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    # The only permitted gaps are the fields the module honestly omits.
    assert set(res.missing_fields) <= set(h._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections
    assert "school_outcomes.employed_or_continuing_ed" in h._OMITTED_INSTITUTION


def test_harvard_hbs_school_is_conformant():
    res = check_conformance("school", _school_snapshot(h._HBS), profile_version=STANDARD_VERSION)
    assert res.conformant, f"HBS gaps: {res.missing_fields} {res.missing_sections}"


def test_harvard_mba_program_is_conformant():
    res = check_conformance(
        "program", _program_snapshot("harvard-mba"), profile_version=STANDARD_VERSION
    )
    assert res.conformant, f"MBA gaps: {res.missing_fields} {res.missing_sections}"


def test_all_twelve_schools_have_about_detail():
    assert {s["name"] for s in h.SCHOOLS} == set(h._SCHOOL_WEBSITE)
    for school in h.SCHOOLS:
        assert h._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"


def test_every_program_maps_to_a_real_school():
    school_names = {s["name"] for s in h.SCHOOLS}
    for spec in h.PROGRAMS:
        assert spec["school"] in school_names, f"{spec['slug']} maps to unknown school"
    assert len(h.PROGRAM_SLUGS) == len(set(h.PROGRAM_SLUGS)), "duplicate program slug"
