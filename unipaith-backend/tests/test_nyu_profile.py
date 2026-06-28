"""The NYU profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 17 schools, and every one of its 507 programs.

Pure (no DB): builds each node's persisted snapshot from the ``nyu_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes when
it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import nyu_profile as n
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST


def _required_fields_of_section(level: str, section_id: str) -> set[str]:
    sec = next(s for s in MANIFEST[level] if s.id == section_id)
    return {f.path for f in sec.fields if f.required and f.enrich}


def _gaps(level: str, res, omitted: set[str]) -> set:
    bad = set(res.missing_fields) - omitted
    for sec_id in res.missing_sections:
        if not _required_fields_of_section(level, sec_id) <= omitted:
            bad |= {f"section:{sec_id}"}
    return bad


def _institution_snapshot() -> dict:
    so = {**n.SCHOOL_OUTCOMES, "_standard": n._standard(n._OMITTED_INSTITUTION)}
    return {
        "description_text": n.DESCRIPTION,
        "student_body_size": n.UNDERGRAD_COUNT,
        "media_gallery": [n.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": n.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": n._INSTITUTION_CONTENT,
    }


def _school_snapshot(spec: dict) -> dict:
    omitted = n._ABOUT_OMITTED.get(spec["name"], [])
    about = {
        **(n._ABOUT_DETAIL.get(spec["name"]) or {}),
        "_standard": n._standard(omitted),
    }
    return {
        "name": spec["name"],
        "description_text": spec["description"],
        "website_url": n._SCHOOL_WEBSITE.get(spec["name"]),
        "about_detail": about,
        "content_sources": n._school_content(spec["name"]),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    tuition, cost = n._program_tuition(spec)
    outcomes = dict(n._OUTCOMES_BY_SLUG.get(slug, {}))
    outcomes["_standard"] = n._program_standard(slug, spec, tuition_omitted=tuition is None)
    kw = n._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(n._SCHOOL_FEED_SPEC[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": spec["website"],
        "department": spec.get("department"),
        "cip_code": n._CIP_BY_SLUG.get(slug),
        "who_its_for": n._WHO_BY_SLUG.get(slug),
        "tracks": None,
        "application_requirements": n._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": n._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": n._FACULTY_BY_SLUG.get(slug),
        "external_reviews": n._REVIEWS_BY_SLUG.get(slug),
        "content_sources": n._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(n.SCHOOLS) == 17
    assert len(n.PROGRAMS) >= 500
    assert len(set(n.PROGRAM_SLUGS)) == len(n.PROGRAM_SLUGS)
    assert any(p["delivery_format"] == "online" for p in n.PROGRAMS)
    assert n.RANKING_DATA["ownership_type"] == "private"
    assert "private research university" in n.DESCRIPTION.lower()
    assert "nyunews.com/feed/" in n._INSTITUTION_CONTENT["news_rss"]
    from unipaith.data.profile_catalog_utils import validate_catalog

    assert not validate_catalog(n.PROGRAMS)


def test_program_names_are_not_scrape_mangled():
    """The bulletin scrape dropped conjunctions, commas, and grade-band dashes from
    multi-field / teacher-certification titles, producing space-mashed names
    ("Economics Computer Science", "Teaching Chemistry 7 12"). REPAIR_BACKLOG CRITICAL
    #1: every name must read as the real published NYU Bulletin title. The structural
    tells are (a) a bare unpunctuated grade-range digit run (" 7 12", " 712", " 5 6 ")
    and (b) a representative set of joint/combined majors that must carry their
    restored conjunction."""
    import re

    mangle_re = re.compile(r"\b\d \d{2}\b|\b[57]12\b|\b\d \d\b")
    bad = [p["program_name"] for p in n.PROGRAMS if mangle_re.search(p["program_name"])]
    assert not bad, f"Scrape-mangled grade ranges in names: {bad[:10]}"

    names = {p["program_name"] for p in n.PROGRAMS}
    must_exist = {
        "Bachelor of Arts in Economics and Computer Science",
        "Bachelor of Arts in French and Linguistics",
        "Bachelor of Arts in Mathematics and Computer Science",
        "Bachelor of Arts in Global Public Health and Anthropology",
        "Bachelor of Science in Health and Wellbeing Studies",
        "Bachelor of Science in Teaching Chemistry 7-12",
        "Master of Arts in Journalism and East Asian Studies",
        "Doctor of Philosophy in French Studies and French",
    }
    missing = must_exist - names
    assert not missing, f"De-mangled joint-major names regressed: {missing}"


def test_no_synthesized_reviews_only_handcrafted():
    """Coverable programs without gathered reviews must omit via _standard, not fake reviews."""
    from scripts.fleet_audit import is_coverable

    synthesized_source = "U.S. News — NYU rankings"
    bad = []
    for p in n.PROGRAMS:
        if not is_coverable(p):
            continue
        slug = p["slug"]
        rev = n._REVIEWS_BY_SLUG.get(slug)
        if not rev:
            continue
        sources = [s.get("url", "") + s.get("label", "") for s in rev.get("sources", [])]
        if any(synthesized_source in str(s) for s in sources):
            bad.append(slug)
    assert not bad, f"Synthesized institution-level reviews: {bad[:10]}"


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(n._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for spec in n.SCHOOLS:
        snap = _school_snapshot(spec)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{spec['name']} gaps: {bad}"


def test_every_program_is_conformant_or_omitted():
    for spec in n.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        tuition, _ = n._program_tuition(spec)
        omitted = set(
            n._program_standard(spec["slug"], spec, tuition_omitted=tuition is None)["omitted"]
        )
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
