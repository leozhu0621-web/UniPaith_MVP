"""The University of Pennsylvania profile (the completed tree) conforms to the gold
standard across every node it models — the institution, twelve schools, and their
twenty-five programs — mirroring the MIT/Sloan/MBAn and Columbia/Chicago/Yale
certifications.

Pure (no DB): builds each node's persisted snapshot from the ``penn_profile`` module the
exact way ``apply()`` writes it, then runs ``check_conformance``. A node passes when it is
gold OR every remaining required field is recorded in that node's ``_standard.omitted``
list with a reason. Penn carries one deeply-enriched flagship (the Wharton MBA); the rest
are catalog programs that report a first-party cost and a Scorecard/institution earnings
figure and omit the uniform insight fields. Every school now carries a program catalog,
and the School of Engineering's MAS-CS is a fully online degree.
"""

from unipaith.data import penn_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance


def _institution_snapshot() -> dict:
    school_outcomes = {**p.SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = p._standard(p._OMITTED_INSTITUTION)
    return {
        "description_text": p.DESCRIPTION,
        "student_body_size": p.UNDERGRAD_COUNT,
        "media_gallery": [p._CAMPUS_PHOTO],
        "ranking_data": {**p.RANKING_DATA},
        "school_outcomes": school_outcomes,
        "content_sources": p._INSTITUTION_CONTENT,
    }


def _school_snapshot(spec: dict) -> dict:
    about = p._ABOUT_DETAIL.get(spec["name"])
    if about is not None:
        about = dict(about)
        about["_standard"] = p._standard(p._ABOUT_OMITTED.get(spec["name"], []))
    return {
        "name": spec["name"],
        "description_text": spec["description"],
        "website_url": p._SCHOOL_WEBSITE.get(spec["name"]),
        "about_detail": about,
        "content_sources": None,
    }


def _program_snapshot(spec: dict) -> dict:
    """Mirror the columns ``_apply_programs`` writes for a program slug."""
    slug = spec["slug"]
    if slug == p._FLAGSHIP:
        outcomes = dict(p._WHARTON_MBA_OUTCOMES)
    else:
        fos = p._FOS_OUTCOMES.get(slug)
        if fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "conditions": p._FOS_CONDITIONS,
                "source": "x",
                "source_url": "x",
            }
        else:
            outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug)
    cost_override = p._COST_BY_SLUG.get(slug)
    cost = dict(cost_override) if cost_override is not None else {
        "tuition_usd": p._TUITION_UG,
        "source": "x",
    }
    return {
        "program_name": p._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": p._WEBSITE_BY_SLUG.get(slug) or p._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": p._HL_BY_SLUG.get(slug) or p._HL_BASELINE,
        "who_its_for": p._WHO_BY_SLUG.get(slug) or p._WHO_BASELINE,
        "tracks": p._TRACKS_BY_SLUG.get(slug),
        "application_requirements": p._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": p._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": p._FACULTY_BY_SLUG.get(slug),
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug),
        "content_sources": p._WHARTON_MBA_CONTENT if slug == p._FLAGSHIP else None,
    }


def _assert_node_done(level: str, snapshot: dict, omitted: set[str], label: str) -> None:
    res = check_conformance(level, snapshot, profile_version=STANDARD_VERSION)
    unrecorded = [f for f in res.missing_fields if f not in omitted]
    assert not unrecorded, f"{level} {label!r} missing un-omitted fields: {unrecorded}"


def test_penn_institution_is_gold_except_recorded_omissions():
    _assert_node_done(
        "institution",
        _institution_snapshot(),
        set(p._OMITTED_INSTITUTION),
        p.INSTITUTION_NAME,
    )


def test_penn_every_school_is_gold_except_recorded_omissions():
    assert len(p.SCHOOLS) == 12
    for spec in p.SCHOOLS:
        _assert_node_done(
            "school",
            _school_snapshot(spec),
            set(p._ABOUT_OMITTED.get(spec["name"], [])),
            spec["name"],
        )


def test_penn_every_program_is_gold_except_recorded_omissions():
    assert len(p.PROGRAMS) == 25
    for spec in p.PROGRAMS:
        _assert_node_done(
            "program",
            _program_snapshot(spec),
            set(p._program_standard(spec["slug"]).get("omitted", [])),
            spec["slug"],
        )


def test_penn_every_school_has_at_least_one_program():
    owners = {spec["school"] for spec in p.PROGRAMS}
    names = {s["name"] for s in p.SCHOOLS}
    assert names - owners == set(), f"schools with no program: {names - owners}"


def test_penn_has_an_online_program_with_delivery_format_set():
    formats = {spec.get("delivery_format", "in_person") for spec in p.PROGRAMS}
    assert "online" in formats
    # Every program declares a delivery_format the card/detail page can render.
    for spec in p.PROGRAMS:
        assert spec.get("delivery_format", "in_person") in {"in_person", "online", "hybrid"}
