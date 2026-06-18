"""The Georgia Tech profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 7 colleges, and every one of its 143 programs — mirroring
the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``georgia_tech_profile``
module exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import georgia_tech_profile as g
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
    so = {**g.SCHOOL_OUTCOMES, "_standard": g._standard(g._OMITTED_INSTITUTION)}
    return {
        "description_text": g.DESCRIPTION,
        "student_body_size": g.UNDERGRAD_COUNT,
        "media_gallery": [g.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": g.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": g._INSTITUTION_CONTENT,
    }


def _school_snapshot(spec: dict) -> dict:
    about = {
        **(g._ABOUT_DETAIL.get(spec["name"]) or {}),
        "_standard": g._standard(g._ABOUT_OMITTED.get(spec["name"], [])),
    }
    return {
        "name": spec["name"],
        "description_text": spec["description"],
        "website_url": g._SCHOOL_WEBSITE.get(spec["name"]),
        "about_detail": about,
        "content_sources": g._school_content(spec["name"]),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    is_ug = spec["degree_type"] == "bachelors"
    if is_ug:
        cost = {
            "tuition_usd": g._TUITION_UG_IN_STATE,
            "total_cost_of_attendance": g._UNDERGRAD_COA,
            "avg_net_price": g._AVG_NET_PRICE,
            "source": g._COST_SRC[0],
            "source_url": g._COST_SRC[1],
        }
    else:
        cost_override = g._COST_BY_SLUG.get(slug)
        cost = cost_override if cost_override is not None else g._grad_cost_fallback(spec)
    if slug == "gatech-mba":
        outcomes = dict(g._MBA_OUTCOMES)
    else:
        outcomes = dict(g._outcomes_for(spec["degree_type"]))
    outcomes["_standard"] = g._program_standard(slug, spec)
    kw = g._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
        g._SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
    )
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": g._website_for(spec),
        "department": spec.get("department"),
        "tracks": g._TRACKS_BY_SLUG.get(slug),
        "application_requirements": g._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": g._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": g._FACULTY_BY_SLUG.get(slug),
        "external_reviews": g._REVIEWS_BY_SLUG.get(slug),
        "content_sources": g._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(g.SCHOOLS) == 7
    assert len(g.PROGRAMS) >= 140
    assert len(set(g.PROGRAM_SLUGS)) == len(g.PROGRAM_SLUGS)
    from unipaith.data.profile_catalog_utils import validate_catalog

    assert not validate_catalog(g.PROGRAMS)
    assert any(p["delivery_format"] == "online" for p in g.PROGRAMS)
    assert g.RANKING_DATA["ownership_type"] == "public"
    assert "public research university" in g.DESCRIPTION.lower()
    assert g._INSTITUTION_CONTENT.get("news_rss") == "https://news.gatech.edu/rss/all"
    assert len(g.SCHOOL_OUTCOMES.get("campus_photos") or []) >= 4


def test_coverable_programs_have_reviews():
    import sys

    sys.path.insert(0, "scripts")
    from fleet_audit import is_coverable

    missing = [
        p["slug"]
        for p in g.PROGRAMS
        if is_coverable(p) and p["slug"] not in g._REVIEWS_BY_SLUG
    ]
    assert not missing, f"Coverable programs missing reviews: {missing[:10]}"


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(g._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"
    assert "school_outcomes.employed_or_continuing_ed" in g._OMITTED_INSTITUTION


def test_every_school_is_conformant():
    for spec in g.SCHOOLS:
        snap = _school_snapshot(spec)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{spec['name']} gaps: {bad}"
        assert snap["content_sources"], f"{spec['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in g.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(g._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_programs_carry_reviews():
    for slug in (
        "gatech-online-ms-computer-science-omscs",
        "gatech-online-ms-analytics",
        "gatech-mba",
        "gatech-computer-science-bs",
        "gatech-industrial-engineering-bs",
        "gatech-analytics-ms",
        "gatech-aerospace-engineering-bs",
    ):
        assert slug in g._REVIEWS_BY_SLUG, f"{slug} should carry external_reviews"
        rev = g._REVIEWS_BY_SLUG[slug]
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]
