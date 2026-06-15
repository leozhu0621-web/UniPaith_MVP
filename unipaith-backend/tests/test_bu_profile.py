"""The BU profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 22 real schools/colleges, and every one of its
programs — mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``bu_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import bu_profile as b
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_COVERABLE_REVIEWS = {
    "bu-academics-cas-computer-science-ba",
    "bu-academics-cds-bs-in-data-science",
    "bu-academics-questrom-mba",
    "bu-academics-law-jd",
    "bu-academics-busm-four-year-program",
    "bu-academics-sdm-doctor-of-dental-medicine",
    "bu-academics-sph-mph",
    "bu-academics-ssw-clinical-social-work-practice",
    "bu-academics-eng-electrical-engineering-bs",
    "bu-academics-com-journalism-bs",
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration",
    "bu-academics-cas-international-relations-ba",
    "bu-academics-com-film-television-film-televisionbs",
    "bu-academics-eng-biomedical-engineering-bs",
    "bu-academics-questrom-ms-in-business-analytics",
    "bu-academics-questrom-ms-in-finance",
    "bu-academics-questrom-mathematical-finance-ms",
    "bu-academics-cds-ms-in-data-science",
    "bu-academics-met-computer-science-ms",
    "bu-academics-met-computer-science-master-of-science-in-applied-data-analytics",
    "bu-academics-eng-computer-engineering-bs",
    "bu-academics-eng-mechanical-engineering-bs",
    "bu-academics-cas-economics-ba",
    "bu-academics-cas-physics-ba",
    "bu-academics-cas-chemistry-ba",
    "bu-academics-cas-psychology-ba",
    "bu-academics-com-journalism-ms",
    "bu-academics-sha-ms",
    "bu-academics-ssw-msw",
    "bu-academics-sph-mba-mph",
    "bu-academics-busm-combined-md-mba",
    "bu-academics-eng-computer-engineering-ms",
    "bu-academics-cas-mathematics-statistics-ba",
    "bu-academics-met-computer-science-bs",
}


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
    so = {**b.SCHOOL_OUTCOMES, "_standard": b._standard(b._OMITTED_INSTITUTION)}
    return {
        "description_text": b.DESCRIPTION,
        "student_body_size": b.UNDERGRAD_COUNT,
        "media_gallery": [b.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": b.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": b._INSTITUTION_CONTENT,
    }


def _school_snapshot(m: dict) -> dict:
    about = {**b._about_for(m), "_standard": b._standard(b._about_omitted(m))}
    return {
        "name": m["name"],
        "description_text": b._school_description(m),
        "website_url": m["website"],
        "about_detail": about,
        "content_sources": b._school_content(m["name"]),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    is_ug = spec["degree_type"] == "bachelors"
    cost = b._undergrad_cost() if is_ug else b._grad_cost_fallback(spec)
    outcomes = dict(b._OUTCOMES_BY_SLUG.get(slug, {}))
    outcomes["_standard"] = b._program_standard(slug, spec)
    kw = b._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(b._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": b._website_for(spec),
        "department": spec.get("department"),
        "tracks": None,
        "application_requirements": b._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": b._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": b._FACULTY_BY_SLUG.get(slug),
        "external_reviews": b._REVIEWS_BY_SLUG.get(slug),
        "content_sources": b._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(b.SCHOOLS) == 22
    assert len(b.PROGRAMS) >= 450
    assert len(set(b.PROGRAM_SLUGS)) == len(b.PROGRAM_SLUGS)
    assert sum(1 for p in b.PROGRAMS if p["delivery_format"] == "online") >= 20
    assert sum(1 for p in b.PROGRAMS if p["degree_type"] == "professional") >= 5
    assert b.RANKING_DATA["ownership_type"] == "private"
    assert "private research university in boston" in b.DESCRIPTION.lower()
    assert len(b.SCHOOL_OUTCOMES["campus_photos"]) >= 4


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(b._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for m in b._SCHOOL_META:
        snap = _school_snapshot(m)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{m['name']} gaps: {bad}"
        assert snap["content_sources"], f"{m['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in b.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(b._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_programs_have_reviews():
    for slug in _COVERABLE_REVIEWS:
        assert slug in b._REVIEWS_BY_SLUG, slug
        assert b._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(b._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_catalog_has_no_padding_stubs():
    """Catalog must not carry bare-abbr / CIP×award-level padding stubs."""
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(b.PROGRAMS)
    assert not errors, f"Catalog padding detected: {errors}"
