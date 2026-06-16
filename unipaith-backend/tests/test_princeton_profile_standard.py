"""The Princeton profile conforms to the gold standard across its whole tree — the
institution, every academic unit, and every program — mirroring the MIT/Sloan/MBAn,
Stanford, Berkeley and Harvard reference certifications.

Pure (no DB): builds each node's persisted snapshot from the princeton_profile module
and runs ``check_conformance``. The only gaps permitted are the fields the module
honestly records in its ``_standard.omitted`` lists.
"""

from unipaith.data import princeton_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "princeton-computer-science-bs"


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
    school_outcomes = {**p.SCHOOL_OUTCOMES}
    for path in p._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            school_outcomes.pop(path.split(".", 1)[1], None)
    school_outcomes["_standard"] = p._standard(p._OMITTED_INSTITUTION)
    return {
        "description_text": p.DESCRIPTION,
        "student_body_size": p.UNDERGRAD_COUNT,
        "media_gallery": [p.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
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
        "content_sources": p._school_content(name),
    }


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = p._SPEC_BY_SLUG[slug]
    fos = p._FOS_OUTCOMES.get(slug)
    if fos is not None:
        salary, cip = fos
        outcomes = {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "conditions": p._FOS_CONDITIONS,
            "source": "x",
        }
    else:
        outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug)
    cost_override = p._COST_BY_SLUG.get(slug)
    cost = dict(cost_override) if cost_override else {"tuition_usd": p._TUITION_UG, "source": "x"}
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
        "class_profile": p._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": p._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": (
            p._CS_CONTENT if slug == _FLAGSHIP else p._program_content(spec)
        ),
    }


def test_princeton_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    omitted = set(p._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    ok, bad = _gaps_are_all_omitted("institution", res, omitted)
    assert ok, f"Unexpected institution section gaps: {bad}"
    assert p.SCHOOL_OUTCOMES.get("media_credit")


def test_institution_has_campus_photo_gallery():
    photos = p.SCHOOL_OUTCOMES.get("campus_photos") or []
    assert len(photos) >= 4, "Princeton needs a 4–5 photo verified campus gallery"
    for photo in photos:
        assert photo.get("url") and photo.get("credit"), photo
    assert p._CAMPUS_PHOTO == photos[0]["url"]


def test_every_school_is_gold_except_recorded_omissions():
    for school in p.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(p._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        ok, bad = _gaps_are_all_omitted("school", res, allowed)
        assert ok, f"{name} unexpected section gaps: {bad}"


def test_flagship_cs_program_is_deeply_enriched():
    res = check_conformance(
        "program", _program_snapshot(_FLAGSHIP), profile_version=STANDARD_VERSION
    )
    assert not res.missing_sections, f"CS missing sections: {res.missing_sections}"
    assert set(res.missing_fields) <= set(p._program_standard(_FLAGSHIP)["omitted"]), (
        f"CS unexpected gaps: {res.missing_fields}"
    )


def test_catalog_has_no_padding_stubs():
    """Every program must have a real department and credential-disambiguated name."""
    import re

    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(p.PROGRAMS)
    assert errors == [], errors
    null_dept = sum(1 for prog in p.PROGRAMS if not prog.get("department"))
    assert null_dept == 0, f"{null_dept} programs missing department"
    prefix = re.compile(
        r"^(Bachelor's in|Master's in|Doctor of Philosophy in|Graduate Certificate in) "
    )
    prefix_count = sum(1 for prog in p.PROGRAMS if prefix.match(prog.get("program_name", "")))
    assert prefix_count == 0, f"{prefix_count} programs still carry CIP-prefix names"
    classif = sum(
        1
        for prog in p.PROGRAMS
        if p._CLASSIFICATION_STUB_RE.match(prog.get("description") or "")
    )
    assert classif == 0, f"{classif} programs still carry classification-only descriptions"


def test_every_program_is_gold_except_recorded_omissions():
    # Real Princeton catalog: ~36 undergraduate majors + verified graduate degrees (M.Arch.,
    # MPA, M.S.E./M.Eng.) — not federal certificate/incidental-master's padding rows.
    assert len(p.PROGRAMS) >= 35, "verified Princeton degree catalog (UNITID 186131)"
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


def test_every_node_has_content_sources():
    assert p._INSTITUTION_CONTENT.get("news_rss")
    assert p._INSTITUTION_CONTENT.get("events_feed")
    for school in p.SCHOOLS:
        cs = p._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), school["name"]
    for spec in p.PROGRAMS:
        cs = p._CS_CONTENT if spec["slug"] == _FLAGSHIP else p._program_content(spec)
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), spec["slug"]


def test_every_program_maps_to_a_real_unit():
    unit_names = {s["name"] for s in p.SCHOOLS}
    for spec in p.PROGRAMS:
        assert spec["school"] in unit_names, f"{spec['slug']} maps to unknown unit"
    assert len(p.PROGRAM_SLUGS) == len(set(p.PROGRAM_SLUGS)), "duplicate program slug"


def test_all_units_have_about_detail():
    assert {s["name"] for s in p.SCHOOLS} == set(p._SCHOOL_WEBSITE)
    for school in p.SCHOOLS:
        assert p._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"


def test_coverable_programs_have_external_reviews():
    """Coverable programs (SPIA, CS, core STEM/engineering, key sciences) must carry reviews."""
    coverable = [
        _FLAGSHIP,
        "princeton-public-affairs-mpa",
        "princeton-public-affairs-ab",
        "princeton-economics-bs",
        "princeton-physics-bs",
        "princeton-mathematics-bs",
        "princeton-electrical-engineering-bs",
        "princeton-mechanical-engineering-bs",
        "princeton-chemical-engineering-bs",
        "princeton-operations-research-bs",
        "princeton-civil-engineering-bs",
        "princeton-architecture-bs",
        "princeton-psychology-bs",
        "princeton-molecular-biology-bs",
        "princeton-neuroscience-bs",
        "princeton-chemistry-bs",
        "princeton-architecture-ms",
        "princeton-chemical-engineering-ms",
        "princeton-civil-engineering-ms",
        "princeton-electrical-electronics-and-communications-engineering-ms",
        "princeton-mechanical-engineering-ms",
    ]
    for slug in coverable:
        assert slug in p._REVIEWS_BY_SLUG, slug
        assert p._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(p._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_institution_research_labs_have_links():
    labs = p.SCHOOL_OUTCOMES.get("research", {}).get("labs", [])
    links = p.SCHOOL_OUTCOMES.get("research", {}).get("lab_links", {})
    for lab in labs:
        assert lab in links, f"Missing lab link for {lab}"


def test_description_leads_with_research_university():
    assert p.DESCRIPTION.startswith(
        "Princeton University is a private research university in Princeton, NJ"
    )
