"""The Johns Hopkins University profile (the completed tree) conforms to the gold standard
across every node it models — the institution, nine degree-granting schools, and their full
published degree catalog — mirroring the MIT / Yale / Princeton reference certifications.

Pure (no DB): builds each node's persisted snapshot from the ``jhu_profile`` module (mirroring
the columns ``apply()`` writes) and runs ``check_conformance``. The only gaps permitted are the
fields each node honestly records in its ``_standard.omitted`` list. The catalog is breadth-
first verified basics — every program omits the same deep/pending fields with reason.
"""

from unipaith.data import jhu_profile as j
from unipaith.profile_standard import STANDARD_VERSION, check_conformance


def _institution_snapshot() -> dict:
    return {
        "description_text": j.DESCRIPTION,
        "student_body_size": j.UNDERGRAD_COUNT,
        "media_gallery": [j._CAMPUS_PHOTO],
        "ranking_data": j.RANKING_DATA,
        "school_outcomes": {**j.SCHOOL_OUTCOMES, "_standard": j._standard(j._OMITTED_INSTITUTION)},
        "content_sources": j._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = j._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = j._standard(j._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in j.SCHOOLS if s["name"] == name),
        "website_url": j._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": j._school_content(name),
    }


def _program_snapshot(spec: dict) -> dict:
    """Mirror the columns _apply_programs writes for a program spec."""
    slug = spec["slug"]
    is_ug = spec["degree_type"] == "bachelors"
    outcomes = dict(j._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = j._program_standard(slug)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": j._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": None,
        "application_requirements": j._requirements_for(spec),
        "cost_data": dict(j._UG_COST) if is_ug else dict(j._GRAD_COST),
        "outcomes_data": outcomes,
        "class_profile": None,
        "faculty_contacts": None,
        "external_reviews": None,
        "content_sources": j._program_content(spec["school"], spec["keywords"]),
    }


def test_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(j._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections


def test_nine_schools_each_gold_except_recorded_omissions():
    assert len(j.SCHOOLS) == 9
    names = {s["name"] for s in j.SCHOOLS}
    assert names == set(j._SCHOOL_WEBSITE)
    for name in names:
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(j._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, f"{name} missing sections: {res.missing_sections}"
        assert j._school_content(name)["news_rss"], f"{name} has no news feed"


def test_every_school_and_program_has_a_working_feed():
    # The empty-Events-&-Updates bug: every school and program must carry a real news_rss so
    # the daily ingest has something to fetch. JHU exposes one verified university RSS (the
    # Hub); every node consumes it filtered by keywords.
    for s in j.SCHOOLS:
        cs = j._school_content(s["name"])
        assert cs["news_rss"] == j._HUB_RSS
        assert cs["keywords"]
    for spec in j.PROGRAMS:
        cs = j._program_content(spec["school"], spec["keywords"])
        assert cs["news_rss"] == j._HUB_RSS
        assert cs["keywords"]


def test_full_catalog_breadth_and_online_coverage():
    # The short-catalog bug: JHU offers well over 100 degree programs across nine schools,
    # including online / professional / continuing-education programs.
    assert len(j.PROGRAMS) >= 180, f"catalog too short: {len(j.PROGRAMS)}"
    assert len(j.PROGRAM_SLUGS) == len(set(j.PROGRAM_SLUGS)), "duplicate program slug"
    formats = {p["delivery_format"] for p in j.PROGRAMS}
    assert "online" in formats and "hybrid" in formats, "missing online/hybrid programs"
    online = [p for p in j.PROGRAMS if p["delivery_format"] in {"online", "hybrid"}]
    assert len(online) >= 40, f"too few online/hybrid programs: {len(online)}"
    for spec in j.PROGRAMS:
        assert spec["delivery_format"] in {"in_person", "online", "hybrid"}, spec["slug"]
        assert spec["degree_type"] in {"bachelors", "masters", "phd", "professional"}


# Whole sections legitimately omittable for breadth-first catalog programs: every field of
# `tracks` (tracks) and `insights` (class_profile / faculty / reviews) is recorded in each
# program's _standard.omitted, so the conformance check reports those two sections as empty.
_OMITTABLE_SECTIONS = {"tracks", "insights"}


def test_every_program_is_gold_except_recorded_omissions():
    unit_names = {s["name"] for s in j.SCHOOLS}
    for spec in j.PROGRAMS:
        assert spec["school"] in unit_names, f"{spec['slug']} -> unknown school {spec['school']}"
        res = check_conformance(
            "program", _program_snapshot(spec), profile_version=STANDARD_VERSION
        )
        allowed = set(j._program_standard(spec["slug"])["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{spec['slug']} unexpected field gaps: {res.missing_fields}"
        )
        assert set(res.missing_sections) <= _OMITTABLE_SECTIONS, (
            f"{spec['slug']} unexpected missing sections: {res.missing_sections}"
        )


def test_every_school_has_published_programs():
    by_school: dict[str, int] = {}
    for spec in j.PROGRAMS:
        by_school[spec["school"]] = by_school.get(spec["school"], 0) + 1
    for s in j.SCHOOLS:
        assert by_school.get(s["name"], 0) >= 1, f"{s['name']} has no programs"
