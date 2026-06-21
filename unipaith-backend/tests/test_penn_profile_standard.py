"""The University of Pennsylvania profile conforms to the gold standard across its
whole tree — the institution, twelve schools, and the full IPEDS/Scorecard program
catalog — mirroring the MIT/Sloan/MBAn and Berkeley reference certifications.

Pure (no DB): builds each node's persisted snapshot from the penn_profile module and runs
``check_conformance``. The only gaps permitted are the fields each node honestly records in
its ``_standard.omitted`` lists. Penn carries a deeply-enriched Wharton MBA flagship plus
coverable external_reviews on every school-flagship and key undergraduate option.
"""

from unipaith.data import penn_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "penn-wharton-mba"
_RESUME_PROGRAMS = {
    "penn-dmd",
    "penn-vmd",
    "penn-march",
    "penn-msw",
    "penn-gse-higher-education-msed",
    "penn-communication-phd",
}


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
        "content_sources": p._school_content(name),
    }


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = p._SPEC_BY_SLUG[slug]
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
    outcomes["_standard"] = p._program_standard(slug, spec)
    cost_override = p._COST_BY_SLUG.get(slug)
    if cost_override is not None:
        cost = dict(cost_override)
    elif is_undergrad:
        cost = {"tuition_usd": p._TUITION_UG, "source": "x"}
    elif spec["degree_type"] in ("masters", "professional", "phd", "certificate"):
        cost = {
            "funded": spec["degree_type"] == "phd",
            "note": "see program website",
            "source": "x",
        }
    else:
        cost = None
    return {
        "program_name": p._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
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
        "content_sources": (
            p._WHARTON_MBA_CONTENT if slug == _FLAGSHIP else p._program_content(spec)
        ),
    }


def test_penn_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    omitted = set(p._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    ok, bad = _gaps_are_all_omitted("institution", res, omitted)
    assert ok, f"Unexpected institution section gaps: {bad}"


def test_every_school_is_gold_except_recorded_omissions():
    assert len(p.SCHOOLS) == 12
    for school in p.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(p._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        ok, bad = _gaps_are_all_omitted("school", res, allowed)
        assert ok, f"{name} unexpected section gaps: {bad}"


def test_wharton_mba_flagship_is_deeply_enriched():
    assert _FLAGSHIP in p._TRACKS_BY_SLUG
    assert _FLAGSHIP in p._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in p._FACULTY_BY_SLUG
    assert _FLAGSHIP in p._REVIEWS_BY_SLUG
    assert p._program_standard(_FLAGSHIP)["omitted"] == []


def test_coverable_programs_have_external_reviews():
    """School flagships, resume programs, and key undergrad options must carry reviews."""
    coverable = [
        _FLAGSHIP,
        "penn-md",
        "penn-jd",
        "penn-dmd",
        "penn-vmd",
        "penn-march",
        "penn-msw",
        "penn-gse-higher-education-msed",
        "penn-communication-phd",
        "penn-computer-science-bse",
        "penn-nursing-bsn",
        "penn-wharton-economics-bs",
        "penn-ppe-ba",
        "penn-bioengineering-bse",
    ]
    for slug in coverable:
        assert slug in p._REVIEWS_BY_SLUG, slug
        assert p._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(p._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_resume_programs_have_external_reviews():
    for slug in _RESUME_PROGRAMS:
        assert slug in p._REVIEWS_BY_SLUG, slug
        omitted = set(p._program_standard(slug, p._SPEC_BY_SLUG[slug])["omitted"])
        assert "external_reviews.summary" not in omitted, slug


def test_every_program_is_gold_except_recorded_omissions():
    # Breadth is asserted by per-row REALNESS (no CIP-rollup / stub padding), NOT a frozen
    # row count — a de-fabrication that drops federal aggregation buckets legitimately
    # SHRINKS the catalog toward the real published list (SKILL miss #2). A peer-scale real
    # catalog still vastly exceeds the gold MIT reference (65); the floor guards a partial
    # build, never a padded count.
    assert len(p.PROGRAMS) >= 150, "Penn real published catalog breadth (UNITID 215062)"
    for spec in p.PROGRAMS:
        slug = spec["slug"]
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        allowed = set(p._program_standard(slug, spec)["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        ok, bad = _gaps_are_all_omitted("program", res, allowed)
        assert ok, f"{slug} unexpected section gaps: {bad}"


def test_every_node_has_content_sources():
    assert p._INSTITUTION_CONTENT.get("news_rss")
    assert p._INSTITUTION_CONTENT.get("events_feed")
    for school in p.SCHOOLS:
        cs = p._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), school["name"]
    for spec in p.PROGRAMS:
        cs = p._WHARTON_MBA_CONTENT if spec["slug"] == _FLAGSHIP else p._program_content(spec)
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), spec["slug"]


def test_resume_programs_carry_verified_cost_and_admissions():
    for slug in _RESUME_PROGRAMS:
        cost = p._COST_BY_SLUG.get(slug)
        assert cost and cost.get("source_url"), f"{slug} missing cited cost"
        assert cost.get("tuition_usd") is not None, f"{slug} missing tuition"
        spec = p._SPEC_BY_SLUG[slug]
        req = p._requirements_for(spec)
        assert req.get("materials") and req.get("source_url"), f"{slug} missing admissions"


def test_every_school_owns_at_least_one_program():
    by_school = {s["name"]: 0 for s in p.SCHOOLS}
    for spec in p.PROGRAMS:
        assert spec["school"] in by_school, f"{spec['slug']} maps to unknown unit"
        by_school[spec["school"]] += 1
    empty = [name for name, n in by_school.items() if n == 0]
    assert not empty, f"schools with no program: {empty}"


def test_catalog_passes_quality_gate():
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(p.PROGRAMS)
    assert not errors, errors
    name_prefix = sum(
        1
        for prog in p.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, f"{name_prefix} programs still prefix description with program_name"


def test_catalog_is_anti_stub_clean():
    """Penn scores gold-MIT-0 on every anti-stub metric, and carries no CIP-rollup name,
    literal CIP code, possessive-mint name, or field-echo department (SKILL miss #2/#8/#9)."""
    import re

    from unipaith.profile_standard import anti_stub

    rows = [
        {"program_name": x["program_name"], "description": x.get("description")}
        for x in p.PROGRAMS
    ]
    report = anti_stub.analyze(rows)
    assert report.is_clean, report.summary()
    assert not anti_stub.machine_artifacts(rows), "machine-artifact descriptions"
    shared = anti_stub.frame_stripped_shared_body(rows, abs_chars=150)
    assert not shared, (
        f"Penn credential siblings share a frame-stripped body on "
        f"{len(shared)} field(s): {shared[:8]}"
    )
    template = anti_stub.template_slot_artifacts(rows)
    assert not template, f"template-slot artifacts on {len(template)} programs"
    possessive = [
        x["program_name"]
        for x in p.PROGRAMS
        if re.match(r"^(Bachelor's|Master's|Doctorate) in ", x["program_name"])
    ]
    assert not possessive, f"possessive-mint names survive: {possessive[:5]}"
    rollup_re = re.compile(r", General\b|, Other\b|, and Linguistics|/")
    rollups = [
        x["program_name"]
        for x in p.PROGRAMS
        if rollup_re.search(p._real_field_of(x["program_name"]))
    ]
    assert not rollups, f"CIP-rollup names survive: {rollups[:5]}"
    cips = [
        x["program_name"]
        for x in p.PROGRAMS
        if "(CIP" in x["program_name"] or "(CIP" in (x.get("department") or "")
    ]
    assert not cips, f"literal CIP codes survive: {cips[:5]}"
    field_echo = [
        x["program_name"]
        for x in p.PROGRAMS
        if (x.get("department") or "") == p._real_field_of(x["program_name"])
    ]
    assert not field_echo, f"field-echo departments survive: {field_echo[:5]}"


def test_every_program_maps_to_a_real_unit_with_unique_slug():
    unit_names = {s["name"] for s in p.SCHOOLS}
    for spec in p.PROGRAMS:
        assert spec["school"] in unit_names, f"{spec['slug']} maps to unknown unit"
    assert len(p.PROGRAM_SLUGS) == len(set(p.PROGRAM_SLUGS)), "duplicate program slug"


def test_all_units_have_about_detail():
    assert {s["name"] for s in p.SCHOOLS} == set(p._SCHOOL_WEBSITE)
    for school in p.SCHOOLS:
        assert p._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"
