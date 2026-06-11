"""The Carnegie Mellon profile conforms to the gold standard for its institution,
every one of its seven schools, and its full breadth-first program catalog.

Pure (no DB): builds each node's persisted snapshot from the
``carnegie_mellon_profile`` module and runs ``check_conformance``. A node is
accepted only when it is gold OR every remaining required field is recorded in
that node's ``_standard.omitted`` (verified-unavailable) with a real reason.
"""

# ruff: noqa: E501

from unipaith.data import carnegie_mellon_profile as c
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST


def _institution_snapshot() -> dict:
    so = {**c.SCHOOL_OUTCOMES}
    for path in c._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            so.pop(path.split(".", 1)[1], None)
    so["_standard"] = c._standard(c._OMITTED_INSTITUTION)
    return {
        "description_text": c.DESCRIPTION,
        "student_body_size": c.UNDERGRAD_COUNT,
        "media_gallery": [c._CAMPUS_PHOTO],
        "ranking_data": c.RANKING_DATA,
        "school_outcomes": so,
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
        "content_sources": None,
    }


def _program_snapshot(spec: dict) -> dict:
    has_tuition = c._tuition_for(spec) is not None
    has_outcomes = spec["degree_type"] in ("bachelors", "masters", "phd")
    outcomes = dict(c._OUTCOMES_INSTITUTION) if has_outcomes else {}
    outcomes["_standard"] = c._program_standard(spec, has_tuition, has_outcomes)
    tuition = c._tuition_for(spec)
    cost = (
        {"tuition_usd": tuition, "source": c._COST_SRC[0], "source_url": c._COST_SRC[1]}
        if tuition is not None
        else None
    )
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": c._description_for(spec),
        "website_url": spec["website_url"],
        "department": spec["department"],
        "tracks": None,
        "application_requirements": c._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": None,
        "faculty_contacts": None,
        "external_reviews": None,
        "content_sources": None,
    }


def _omitted_for(spec: dict) -> set[str]:
    has_tuition = c._tuition_for(spec) is not None
    has_outcomes = spec["degree_type"] in ("bachelors", "masters", "phd")
    return set(c._program_standard(spec, has_tuition, has_outcomes)["omitted"])


def _section_gaps_unexpected(level: str, missing_sections: list[str], omitted: set[str]) -> list:
    """A missing required section is acceptable only when ALL its required
    enrich-fields are recorded in this node's omitted list."""
    bad = []
    for secid in missing_sections:
        sec = next(s for s in MANIFEST[level] if s.id == secid)
        req = {f.path for f in sec.fields if f.enrich and f.required}
        if not req <= omitted:
            bad.append(secid)
    return bad


def test_institution_is_gold_except_recorded_omissions():
    res = check_conformance("institution", _institution_snapshot(), profile_version=STANDARD_VERSION)
    omitted = set(c._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, f"Unexpected institution gaps: {res.missing_fields}"
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)
    # The two honestly-omitted institution outcome fields.
    assert "school_outcomes.employed_or_continuing_ed" in omitted
    assert "school_outcomes.top_employer_industries" in omitted


def test_all_seven_schools_done():
    assert len(c.SCHOOLS) == 7
    assert {s["name"] for s in c.SCHOOLS} == set(c._SCHOOL_WEBSITE)
    for school in c.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(c._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, f"{name}: unexpected gaps {res.missing_fields}"
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name


def test_every_program_is_done():
    assert len(c.PROGRAMS) >= 150, "breadth-first catalog should be the full program set"
    for spec in c.PROGRAMS:
        res = check_conformance("program", _program_snapshot(spec), profile_version=STANDARD_VERSION)
        omitted = _omitted_for(spec)
        assert set(res.missing_fields) <= omitted, f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), spec["slug"]


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in c.SCHOOLS}
    for spec in c.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(c.PROGRAM_SLUGS) == len(set(c.PROGRAM_SLUGS)), "duplicate program slug"


def test_every_program_has_delivery_format():
    assert {p["delivery_format"] for p in c.PROGRAMS} <= {"in_person", "online", "hybrid"}
    for spec in c.PROGRAMS:
        assert spec["delivery_format"], f"{spec['slug']} missing delivery_format"
    # the catalog includes online + hybrid + bicoastal/multi-campus programs
    assert any(p["delivery_format"] == "online" for p in c.PROGRAMS)
    assert any(p["delivery_format"] == "hybrid" for p in c.PROGRAMS)
