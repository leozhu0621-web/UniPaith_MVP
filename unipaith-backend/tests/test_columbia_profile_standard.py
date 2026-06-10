"""The Columbia University profile (this run's verified partial) conforms to the gold
standard across the nodes it models — the institution, five schools, and their programs —
mirroring the MIT/Sloan/MBAn and the Chicago/Yale reference certifications.

Pure (no DB): builds each node's persisted snapshot from the columbia_profile module and
runs ``check_conformance``. The only gaps permitted are the fields the module honestly
records in its ``_standard.omitted`` lists. The flagship is the Columbia Business School
MBA. (Columbia is a giant; the remaining schools/programs are deferred to a resume run.)
"""

from unipaith.data import columbia_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

_FLAGSHIP = "columbia-mba"


def _institution_snapshot() -> dict:
    school_outcomes = {**p.SCHOOL_OUTCOMES}
    for path in p._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            rest = path.split(".", 1)[1]
            if "." not in rest:
                school_outcomes.pop(rest, None)
            else:
                head, leaf = rest.split(".", 1)
                if isinstance(school_outcomes.get(head), dict):
                    school_outcomes[head].pop(leaf, None)
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
    outcomes = p._outcomes_for(slug)
    outcomes["_standard"] = p._program_standard(slug)
    cost_override = p._COST_BY_SLUG.get(slug)
    cost = dict(cost_override) if cost_override else {"tuition_usd": p._TUITION_UG, "source": "x"}
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
        "class_profile": p._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": p._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": p._MBA_CONTENT if slug == _FLAGSHIP else None,
    }


def test_columbia_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(p._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections
    assert "school_outcomes.scale.faculty_count" in p._OMITTED_INSTITUTION


def test_every_school_is_gold_except_recorded_omissions():
    for school in p.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(p._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, f"{name} missing sections: {res.missing_sections}"


def test_flagship_mba_program_is_conformant():
    res = check_conformance(
        "program", _program_snapshot(_FLAGSHIP), profile_version=STANDARD_VERSION
    )
    assert not res.missing_sections, f"MBA missing sections: {res.missing_sections}"
    assert set(res.missing_fields) <= set(p._program_standard(_FLAGSHIP)["omitted"]), (
        f"MBA unexpected gaps: {res.missing_fields}"
    )
    assert not p._program_standard(_FLAGSHIP)["omitted"], "flagship should have no omissions"


def test_every_program_is_gold_except_recorded_omissions():
    omittable_sections = {"tracks", "insights", "feeds"}
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


def test_every_program_maps_to_a_real_unit():
    unit_names = {s["name"] for s in p.SCHOOLS}
    for spec in p.PROGRAMS:
        assert spec["school"] in unit_names, f"{spec['slug']} maps to unknown unit"
    assert len(p.PROGRAM_SLUGS) == len(set(p.PROGRAM_SLUGS)), "duplicate program slug"


def test_all_units_have_about_detail():
    assert {s["name"] for s in p.SCHOOLS} == set(p._SCHOOL_WEBSITE)
    for school in p.SCHOOLS:
        assert p._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"
