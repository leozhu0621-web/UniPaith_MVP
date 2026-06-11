"""The Carnegie Mellon profile conforms to the gold standard across its WHOLE tree —
the institution, every one of its real colleges/schools, and every program — mirroring
the MIT/Sloan/MBAn reference certification in test_profile_standard.

Pure (no DB): builds each node's persisted snapshot from the cmu_profile module exactly
as ``apply()`` writes it, and runs ``check_conformance``. A node passes when it is gold
OR every remaining required gap is recorded in that node's ``_standard.omitted`` (the
omit-with-reason gate).
"""

from unipaith.data import cmu_profile as cu
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST


def _required_fields_of_section(level: str, section_id: str) -> set[str]:
    sec = next(s for s in MANIFEST[level] if s.id == section_id)
    return {f.path for f in sec.fields if f.required and f.enrich}


def _gaps_are_all_omitted(level: str, res, omitted: set[str]) -> tuple[bool, set]:
    """A node is acceptable when every missing field is omitted AND every missing
    section has *all* its required fields omitted."""
    bad = set(res.missing_fields) - omitted
    for sec_id in res.missing_sections:
        if not _required_fields_of_section(level, sec_id) <= omitted:
            bad |= {f"section:{sec_id}"}
    return (not bad), bad


def _default_cost() -> dict:
    return {
        "tuition_usd": cu._TUITION,
        "total_cost_of_attendance": cu._UNDERGRAD_COA,
        "avg_net_price": cu._AVG_NET_PRICE,
        "breakdown": {"tuition": cu._TUITION, "fees": cu._FEES, "room_board": cu._ROOM_BOARD},
        "source": "Carnegie Mellon Common Data Set 2024-25 (§G1)",
        "source_url": "https://www.cmu.edu/ira/CDS/cds_2425.html",
    }


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = next(p for p in cu.PROGRAMS if p["slug"] == slug)
    cost = cu._COST_BY_SLUG.get(slug) or _default_cost()
    outcomes = dict(cu._OUTCOMES_INSTITUTION)
    return {
        "program_name": cu._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": "bachelors",
        "duration_months": spec.get("duration_months", 48),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": cu._WEBSITE_BY_SLUG.get(slug) or cu._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": cu._HL_BY_SLUG.get(slug) or cu._HL_BASELINE,
        "who_its_for": cu._WHO_BY_SLUG.get(slug) or cu._WHO_BASELINE,
        "tracks": cu._TRACKS_BY_SLUG.get(slug),
        "application_requirements": cu._REQ_UNDERGRAD,
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": None,
        "faculty_contacts": cu._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": cu._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": cu._CS_CONTENT if slug == "cmu-computer-science-bs" else None,
    }


def _school_snapshot(name: str) -> dict:
    return {
        "name": name,
        "description_text": next(s["description"] for s in cu.SCHOOLS if s["name"] == name),
        "website_url": cu._SCHOOL_WEBSITE.get(name),
        "about_detail": cu._ABOUT_DETAIL.get(name),
        "content_sources": None,
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


def test_cmu_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    ok, bad = _gaps_are_all_omitted("institution", res, set(cu._OMITTED_INSTITUTION))
    assert ok, f"Unexpected institution gaps: {bad}"
    # The report-card, funnel, diversity, scale, cost & aid and feeds sections render.
    assert "school_outcomes.employed_or_continuing_ed" in cu._OMITTED_INSTITUTION
    assert cu.SCHOOL_OUTCOMES["admit_rate"] and cu.RANKING_DATA["ownership_type"] == "private"


def test_every_school_is_conformant():
    for school in cu.SCHOOLS:
        snap = _school_snapshot(school["name"])
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        allowed = set(cu._ABOUT_OMITTED.get(school["name"], []))
        ok, bad = _gaps_are_all_omitted("school", res, allowed)
        assert ok, f"{school['name']} gaps: {bad}"


def test_every_program_is_conformant_or_omitted():
    for spec in cu.PROGRAMS:
        slug = spec["slug"]
        snap = _program_snapshot(slug)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(cu._program_standard(slug)["omitted"])
        ok, bad = _gaps_are_all_omitted("program", res, omitted)
        assert ok, f"{slug} has un-omitted gaps: {bad}"


def test_flagship_cs_program_carries_tracks_faculty_reviews_feed():
    """The flagship CS B.S. carries tracks, faculty, reviews and its own feed; the only
    omitted gaps are the program-level employment rate, industry mix and per-major cohort
    size, which CMU does not publish per-program."""
    slug = "cmu-computer-science-bs"
    res = check_conformance("program", _program_snapshot(slug), profile_version=STANDARD_VERSION)
    omitted = set(cu._program_standard(slug)["omitted"])
    ok, bad = _gaps_are_all_omitted("program", res, omitted)
    assert ok, f"flagship unexpected gaps: {bad}"
    assert "tracks" not in omitted  # tracks ARE published for CS
    assert "faculty_contacts.lead" not in omitted
    assert "external_reviews.summary" not in omitted
    assert omitted == {
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "class_profile.cohort_size",
    }


def test_structure_integrity():
    school_names = {s["name"] for s in cu.SCHOOLS}
    for spec in cu.PROGRAMS:
        assert spec["school"] in school_names, f"{spec['slug']} maps to unknown school"
    assert school_names == set(cu._SCHOOL_WEBSITE)
    for school in cu.SCHOOLS:
        assert cu._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"
    assert len(cu.PROGRAM_SLUGS) == len(set(cu.PROGRAM_SLUGS)), "duplicate program slug"
    # Every program sets a delivery_format (CMU's undergraduate catalog is on-campus).
    fmts = {p.get("delivery_format", "in_person") for p in cu.PROGRAMS}
    assert fmts == {"in_person"}
    # A substantial catalog across the six undergraduate colleges.
    assert len(cu.PROGRAMS) >= 30


def test_every_node_has_standard_stamp():
    assert cu._standard(cu._OMITTED_INSTITUTION)["version"] == STANDARD_VERSION
    for spec in cu.PROGRAMS:
        st = cu._program_standard(spec["slug"])
        assert st["version"] == STANDARD_VERSION and st["enriched_at"] == cu.ENRICHED_AT
