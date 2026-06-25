"""The Columbia University profile conforms to the gold standard across its whole tree —
the institution, fourteen schools, and the full real degree catalog (rebuilt 2026-06-19,
columbiadefab1, replacing the IPEDS×award-level padding) — mirroring the MIT/Sloan/MBAn
and the Chicago/Yale reference certifications.

Pure (no DB): builds each node's persisted snapshot from the columbia_profile module and
runs ``check_conformance``. The only gaps permitted are the fields each node honestly
records in its ``_standard.omitted`` lists. Columbia carries two deeply-enriched
flagships: undergraduate Computer Science and the Columbia Business School MBA.
"""

from unipaith.data import columbia_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

_CS_FLAGSHIP = "columbia-computer-science-bs"
_MBA_FLAGSHIP = "columbia-mba"


def _institution_snapshot() -> dict:
    school_outcomes = {**p.SCHOOL_OUTCOMES}
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
    spec = next(pr for pr in p.PROGRAMS if pr["slug"] == slug)
    is_undergrad = spec["degree_type"] == "bachelors"
    if slug == "columbia-md":
        salary, cip = p._MD_OUTCOME
        outcomes = {"median_salary": salary, "scope": "program", "cip": cip,
                    "conditions": p._FOS_CONDITIONS, "source": "x", "source_url": "x"}
    else:
        fos = p._FOS_OUTCOMES.get(slug)
        if fos is not None:
            outcomes = {"median_salary": fos[0], "scope": "program", "cip": fos[1],
                        "conditions": p._FOS_CONDITIONS, "source": "x", "source_url": "x"}
        else:
            outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug)
    cost_override = p._COST_BY_SLUG.get(slug)
    if is_undergrad:
        cost = {"tuition_usd": p._TUITION_UG, "source": "x"}
    elif cost_override is not None:
        cost = dict(cost_override)
    else:
        cost = None
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
        "content_sources": p._program_content(spec),
    }


def test_columbia_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(p._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections


def test_every_school_is_gold_except_recorded_omissions():
    assert len(p.SCHOOLS) == 14
    for school in p.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(p._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, f"{name} missing sections: {res.missing_sections}"


def test_two_flagships_are_deeply_enriched():
    # Both flagships carry curriculum, class profile, faculty, reviews and their own feed —
    # so the only recorded omissions are the college-wide employment fields.
    for slug in (_CS_FLAGSHIP, _MBA_FLAGSHIP):
        assert slug in p._TRACKS_BY_SLUG
        assert slug in p._CLASS_PROFILE_BY_SLUG
        assert slug in p._FACULTY_BY_SLUG
        assert slug in p._REVIEWS_BY_SLUG
        spec = next(pr for pr in p.PROGRAMS if pr["slug"] == slug)
        cs = p._program_content(spec)
        assert cs.get("news_rss"), f"{slug} missing news_rss"
        assert cs.get("keywords"), f"{slug} missing keywords"
        assert set(p._program_standard(slug)["omitted"]) == {
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        }


def test_every_school_and_program_has_content_sources():
    for school in p.SCHOOLS:
        cs = p._school_content(school["name"])
        assert cs.get("news_rss"), f"{school['name']} missing news_rss"
        assert cs.get("keywords"), f"{school['name']} missing keywords"
    for spec in p.PROGRAMS:
        cs = p._program_content(spec)
        assert cs.get("news_rss"), f"{spec['slug']} missing news_rss"
        assert cs.get("keywords"), f"{spec['slug']} missing keywords"


def test_catalog_quality_gate():
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(p.PROGRAMS)
    assert not errors, f"Catalog quality gate failed: {errors}"


def test_full_catalog_breadth():
    # Real catalog floor — peer-level breadth across the 14 schools (cf. MIT 65). The
    # prior >= 250 figure was calibrated to the IPEDS×award-level PADDING (263 rows, 88 of
    # them fabricated departmental "certificates" + possessive CIP-rollup names); the
    # de-fabricated real catalog legitimately shrinks toward Columbia's published degrees,
    # so breadth is enforced by per-row REALNESS below, not a frozen padded count
    # (SKILL.md miss #2).
    assert len(p.PROGRAMS) >= 150, f"catalog too short: {len(p.PROGRAMS)}"
    assert len(p.PROGRAM_SLUGS) == len(set(p.PROGRAM_SLUGS)), "duplicate program slug"
    for spec in p.PROGRAMS:
        assert spec.get("delivery_format") in {"on_campus", "online", "hybrid"}, spec["slug"]
        assert spec.get("department"), f"{spec['slug']} missing department"


def test_catalog_is_structurally_real():
    """Per-row realness gate (replaces the frozen padded-count assertion, SKILL.md miss #2):
    no possessive-mint names, no bare CIP-rollup / award-level names, conferred designations."""
    import re

    from unipaith.profile_standard.anti_stub import analyze, field_of, machine_artifacts

    report = analyze(p.PROGRAMS)
    assert report.is_clean, f"anti-stub not clean: {report.summary()}"
    assert not machine_artifacts(p.PROGRAMS), "build-artifact junk in descriptions"
    for spec in p.PROGRAMS:
        name = spec["program_name"]
        assert not re.match(r"^(Bachelor's|Master's|Doctorate) in ", name), (
            f"possessive-mint name: {name}"
        )
        field = field_of(name)
        assert not re.search(r", General$|, Other$", field), f"CIP rollup tell in {name}"
        # department is never the field echoed verbatim from the name
        assert spec["department"] != field, f"field-echo department: {spec['slug']}"


def test_every_program_is_gold_except_recorded_omissions():
    omittable_sections = {"tracks", "costs", "insights", "feeds"}
    assert len(p.PROGRAMS) >= 150, f"real catalog breadth: {len(p.PROGRAMS)}"
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


def test_coverable_programs_have_external_reviews():
    """Coverable programs (MBA, CS, JD, MD, MPH, MPA, MArch, MSW, economics) must carry reviews."""
    coverable = [
        _MBA_FLAGSHIP,
        _CS_FLAGSHIP,
        "columbia-jd",
        "columbia-md",
        "columbia-public-health-mph",
        "columbia-economics-ba",
        "columbia-journalism-ms",
        "columbia-sipa-mpa",
        "columbia-architecture-march",
        "columbia-social-work-msw",
    ]
    for slug in coverable:
        assert slug in p._REVIEWS_BY_SLUG, slug
        assert p._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(p._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_institution_has_media_credit():
    assert p.SCHOOL_OUTCOMES.get("media_credit"), "campus photo must carry attribution"


def test_institution_has_campus_photo_gallery():
    photos = p.SCHOOL_OUTCOMES.get("campus_photos") or []
    assert len(photos) >= 4, "Columbia needs a 4–5 photo verified campus gallery"
    for photo in photos:
        assert photo.get("url") and photo.get("credit"), photo
    assert p._CAMPUS_PHOTO == photos[0]["url"]


def test_description_leads_with_research_university():
    assert p.DESCRIPTION.startswith(
        "Columbia University is a private research university in New York, NY"
    )


def test_no_name_prefixed_descriptions():
    name_prefix = sum(
        1
        for prog in p.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, (
        f"{name_prefix} programs still prefix description with program_name"
    )


def test_no_identical_across_credential_levels():
    from collections import Counter

    desc_counts = Counter(prog.get("description") for prog in p.PROGRAMS)
    shared = sum(c for c in desc_counts.values() if c >= 2)
    assert shared == 0, (
        f"{shared} programs share a description verbatim with a credential sibling"
    )


def test_no_peer_contaminated_descriptions():
    peer = sum(
        1
        for prog in p.PROGRAMS
        if any(sig in (prog.get("description") or "") for sig in p._PEER_SIGNATURES)
    )
    assert peer == 0, f"{peer} programs still carry peer-institution contamination"


def test_every_program_carries_a_matcher_core_cip_code():
    """Matcher-core CIP coverage gate (REPAIR_BACKLOG #1): every program carries a verified
    NCES CIP-2020 code (family NN.NN or detail NN.NNNN) — the CIP join key the CPEF matcher
    reads (2-digit family) for the field/interest signal. A catalog-wide null is matcher
    starvation, not an honest omission; there are no genuinely uncodeable programs today."""
    import re

    missing = [spec["slug"] for spec in p.PROGRAMS if not spec.get("cip")]
    assert not missing, f"{len(missing)} programs missing cip_code: {missing[:8]}"
    bad = sorted(
        {
            spec["cip"]
            for spec in p.PROGRAMS
            if not re.fullmatch(r"\d{2}\.\d{2}(\d{2})?", spec["cip"])
        }
    )
    assert not bad, f"malformed cip_code values: {bad}"
