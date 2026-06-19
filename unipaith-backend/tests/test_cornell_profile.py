"""The Cornell profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its real colleges/schools, and every program — mirroring the
MIT/Sloan/MBAn reference certification in test_profile_standard.

Pure (no DB): builds each node's persisted snapshot from the cornell_profile module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes when it
is gold OR every remaining required gap is recorded in that node's ``_standard.omitted``.
"""

import re

from unipaith.data import cornell_profile as cu
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.anti_stub import field_of
from unipaith.profile_standard.manifest import MANIFEST

# CIP-taxonomy rollup tells that must never appear in a real program_name or department
# (enrich-profile miss #2). Anchored to federal taxonomy endings so real Oxford-comma
# majors are not false-flagged.
_ROLLUP_TELL = re.compile(
    r", (General|Other)\b"
    r"|, and (Group Studies|Linguistics|Administration|Technicians)\b"
    r"|, Literatures, and\b"
    r"|, Pharmaceutical Sciences, and\b"
    r"|[A-Za-z]/[A-Za-z]"
)


def _assert_no_cip_rollup_names(programs: list[dict]) -> None:
    bad = [
        p["program_name"]
        for p in programs
        if _ROLLUP_TELL.search(field_of(p["program_name"]))
        or _ROLLUP_TELL.search(p.get("department") or "")
    ]
    assert not bad, f"{len(bad)} programs still carry a CIP-rollup name/department: {bad[:5]}"


def _required_fields_of_section(level: str, section_id: str) -> set[str]:
    """The dotted paths a section needs (this profile's own required+enrich fields)."""
    sec = next(s for s in MANIFEST[level] if s.id == section_id)
    return {f.path for f in sec.fields if f.required and f.enrich}


def _gaps_are_all_omitted(level: str, res, omitted: set[str]) -> tuple[bool, set]:
    """A node is acceptable when every missing field is omitted AND every missing section
    has *all* its required fields omitted (the omit-with-reason gate)."""
    bad = set(res.missing_fields) - omitted
    for sec_id in res.missing_sections:
        if not _required_fields_of_section(level, sec_id) <= omitted:
            bad |= {f"section:{sec_id}"}
    return (not bad), bad


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = next(p for p in cu.PROGRAMS if p["slug"] == slug)
    cost = cu._cost_for(spec)
    if cost is None:
        cost = {"funded": False, "note": "see program website", "source": "x", "source_url": "x"}
    if slug == cu._FLAGSHIP:
        outcomes = dict(cu._MBA_OUTCOMES)
    else:
        fos = cu._FOS_OUTCOMES.get(slug)
        if fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "conditions": cu._FOS_CONDITIONS,
                "source": "College Scorecard",
                "source_url": "x",
            }
        else:
            outcomes = dict(cu._OUTCOMES_INSTITUTION)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": cu._WEBSITE_BY_SLUG.get(slug) or cu._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": cu._HL_BY_SLUG.get(slug) or cu._HL_BASELINE,
        "who_its_for": cu._WHO_BY_SLUG.get(slug) or cu._WHO_BASELINE,
        "tracks": cu._TRACKS_BY_SLUG.get(slug),
        "application_requirements": cu._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": cu._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": cu._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": cu._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": (
            cu._CS_CONTENT
            if slug == "cornell-computer-science-bs"
            else (cu._MBA_CONTENT if slug == cu._FLAGSHIP else cu._program_content(spec))
        ),
    }


def _school_snapshot(name: str) -> dict:
    return {
        "name": name,
        "description_text": next(s["description"] for s in cu.SCHOOLS if s["name"] == name),
        "website_url": cu._SCHOOL_WEBSITE.get(name),
        "about_detail": cu._ABOUT_DETAIL.get(name),
        "content_sources": cu._school_content(name),
    }


def _institution_snapshot() -> dict:
    return {
        "description_text": cu.DESCRIPTION,
        "student_body_size": cu.UNDERGRAD_COUNT,
        "media_gallery": [cu._CAMPUS_PHOTO],
        "ranking_data": cu.RANKING_DATA,
        "school_outcomes": cu.SCHOOL_OUTCOMES,
        "content_sources": cu._INSTITUTION_CONTENT,
    }


def test_catalog_quality_gate():
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(cu.PROGRAMS)
    assert not errors, f"Catalog quality gate failed: {errors}"
    possessive = [
        p["program_name"]
        for p in cu.PROGRAMS
        if cu._POSSESSIVE_NAME_RE.match(p.get("program_name", ""))
    ]
    assert not possessive, (
        f"{len(possessive)} programs still carry possessive-mint names: {possessive[:5]}"
    )
    classif = sum(
        1
        for prog in cu.PROGRAMS
        if cu._CLASSIFICATION_STUB_RE.match(prog.get("description") or "")
    )
    assert classif == 0, f"{classif} programs still carry classification-only descriptions"
    name_prefix = sum(
        1
        for prog in cu.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, f"{name_prefix} programs still prefix description with program_name"


def test_catalog_has_no_peer_institution_signatures():
    """Regression guard: descriptions must not carry foreign-university unit names."""
    contaminated = [
        p["slug"]
        for p in cu.PROGRAMS
        if any(sig in (p.get("description") or "") for sig in cu._PEER_SIGNATURES)
    ]
    assert not contaminated, (
        f"{len(contaminated)} programs still carry peer-institution signatures: "
        f"{contaminated[:5]}"
    )


def test_catalog_breadth_and_shape():
    assert len(cu.SCHOOLS) == 14
    # Breadth is a REALNESS gate, not a frozen count: de-fabricating the Scorecard rollup
    # buckets (federal "Other"/"General" CIP titles → real Cornell degrees or dropped)
    # legitimately shrinks the catalog below the old padded 260 (enrich-profile miss #2).
    assert len(cu.PROGRAMS) >= 235
    _assert_no_cip_rollup_names(cu.PROGRAMS)
    assert len(set(cu.PROGRAM_SLUGS)) == len(cu.PROGRAM_SLUGS)
    assert cu.RANKING_DATA["ownership_type"] == "private"
    desc = cu.DESCRIPTION.lower()
    assert "private" in desc and "research university in ithaca" in desc
    assert len(cu.SCHOOL_OUTCOMES["campus_photos"]) >= 4


def test_cornell_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(cu._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections
    assert "school_outcomes.flagship.admits" in cu._OMITTED_INSTITUTION


def test_every_school_is_conformant():
    for school in cu.SCHOOLS:
        snap = _school_snapshot(school["name"])
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = (snap["about_detail"] or {}).get("_standard", {}).get("omitted", [])
        # The school snapshot's about_detail _standard isn't built here, so allow the
        # known per-school omission (notable faculty) which is recorded in apply().
        allowed = set(omitted) | set(cu._ABOUT_OMITTED.get(school["name"], []))
        assert set(res.missing_fields) <= allowed, (
            f"{school['name']} gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, (
            f"{school['name']} missing sections: {res.missing_sections}"
        )


def test_every_program_is_conformant_or_omitted():
    for spec in cu.PROGRAMS:
        slug = spec["slug"]
        snap = _program_snapshot(slug)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(cu._program_standard(slug, spec)["omitted"])
        ok, bad = _gaps_are_all_omitted("program", res, omitted)
        assert ok, f"{slug} has un-omitted gaps: {bad}"


def test_flagship_cs_program_is_gold_except_universitywide_outcomes():
    """The flagship CS B.S. carries every program section (tracks, insights, feeds); the
    only gaps are the program-level employment rate and industry mix, which Cornell does
    not publish per-program (reported university-wide) and are recorded as omitted."""
    slug = "cornell-computer-science-bs"
    spec = next(p for p in cu.PROGRAMS if p["slug"] == slug)
    res = check_conformance("program", _program_snapshot(slug), profile_version=STANDARD_VERSION)
    omitted = set(cu._program_standard(slug, spec)["omitted"])
    assert not res.missing_sections, f"flagship missing whole sections: {res.missing_sections}"
    assert set(res.missing_fields) <= omitted, (
        f"flagship unexpected gaps: {set(res.missing_fields) - omitted}"
    )
    assert omitted == {"outcomes_data.employment_rate", "outcomes_data.top_industries"}


def test_structure_integrity():
    school_names = {s["name"] for s in cu.SCHOOLS}
    # Every program maps to a real school.
    for spec in cu.PROGRAMS:
        assert spec["school"] in school_names, f"{spec['slug']} maps to unknown school"
    # Every school has about_detail and a website.
    assert school_names == set(cu._SCHOOL_WEBSITE)
    for school in cu.SCHOOLS:
        assert cu._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"
    # Slugs are unique.
    assert len(cu.PROGRAM_SLUGS) == len(set(cu.PROGRAM_SLUGS)), "duplicate program slug"
    # Full catalog breadth: College Scorecard Field-of-Study list for UNITID 190415.
    assert len(cu.PROGRAMS) >= 235, "verified real Cornell catalog breadth (de-padded)"
    # Every program sets a delivery_format, and at least one online + one hybrid exist.
    fmts = {p.get("delivery_format") for p in cu.PROGRAMS}
    assert None not in fmts
    assert "online" in fmts and "hybrid" in fmts and "in_person" in fmts


def test_every_node_has_content_sources():
    assert cu._INSTITUTION_CONTENT.get("news_rss")
    for school in cu.SCHOOLS:
        cs = cu._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), school["name"]
    for spec in cu.PROGRAMS:
        cs = (
            cu._CS_CONTENT
            if spec["slug"] == "cornell-computer-science-bs"
            else cu._program_content(spec)
        )
        assert cs.get("news_rss") and cs.get("keywords"), spec["slug"]


def test_every_node_has_standard_stamp():
    # Institution stamp is applied in apply(); verify the omitted list is wired.
    assert cu._standard(cu._OMITTED_INSTITUTION)["version"] == STANDARD_VERSION
    for spec in cu.PROGRAMS:
        st = cu._program_standard(spec["slug"], spec)
        assert st["version"] == STANDARD_VERSION and st["enriched_at"] == cu.ENRICHED_AT


def test_institution_has_media_credit():
    assert cu.SCHOOL_OUTCOMES.get("media_credit"), "Campus photo must carry attribution"


def test_coverable_programs_have_reviews():
    """Thirteen coverable programs carry aggregated external_reviews (not merely omitted)."""
    expected = {
        "cornell-computer-science-bs",
        "cornell-mba",
        "cornell-computer-science-ms",
        "cornell-jd",
        "cornell-dvm",
        "cornell-md",
        "cornell-hotel-administration-bs",
        "cornell-emba-americas",
        "cornell-ilr-bs",
        "cornell-economics-bs",
        "cornell-applied-economics-bs",
        "cornell-electrical-computer-eng-ms",
        "cornell-mechanical-eng-bs",
    }
    reviewed = {
        slug for slug, rev in cu._REVIEWS_BY_SLUG.items() if rev and rev.get("summary")
    }
    assert expected <= reviewed, f"Missing reviews for {expected - reviewed}"
    for slug in expected:
        assert len(cu._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_johnson_mba_flagship_is_deeply_enriched():
    slug = cu._FLAGSHIP
    spec = next(p for p in cu.PROGRAMS if p["slug"] == slug)
    snap = _program_snapshot(slug)
    res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
    omitted = set(cu._program_standard(slug, spec)["omitted"])
    assert res.conformant or set(res.missing_fields) <= omitted, (
        f"MBA gaps: {set(res.missing_fields) - omitted}"
    )
    assert cu._MBA_OUTCOMES["median_salary"] == 175000
    assert snap["external_reviews"].get("summary")
    assert snap["tracks"] is not None
    assert snap["class_profile"].get("cohort_size")
