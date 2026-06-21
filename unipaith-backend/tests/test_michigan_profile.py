"""The Michigan profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 19 schools/colleges, and every one of its 379
programs — mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``michigan_profile``
module exactly as ``apply()`` writes it, and runs ``check_conformance``. A node
passes when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import michigan_profile as m
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
    so = {**m.SCHOOL_OUTCOMES, "_standard": m._standard(m._OMITTED_INSTITUTION)}
    return {
        "description_text": m.DESCRIPTION,
        "student_body_size": m.UNDERGRAD_COUNT,
        "media_gallery": [m.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": m.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": m._INSTITUTION_CONTENT,
    }


def _school_snapshot(spec: dict) -> dict:
    meta = next(x for x in m._SCHOOL_META if x["name"] == spec["name"])
    about = {**m._about_for(meta), "_standard": m._standard(m._about_omitted(meta))}
    return {
        "name": spec["name"],
        "description_text": spec["description"],
        "website_url": m.SCHOOL_WEBSITE.get(spec["name"]),
        "about_detail": about,
        "content_sources": m._school_content(spec["name"]),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    is_ug = spec["degree_type"] == "bachelors"
    cost = m._undergrad_cost() if is_ug else m._grad_cost_fallback(spec)
    outcomes = dict(m._OUTCOMES_BY_SLUG.get(slug, {}))
    outcomes["_standard"] = m._program_standard(slug, spec)
    kw = m._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(m._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": m._website_for(spec),
        "department": spec.get("department"),
        "tracks": None,
        "application_requirements": m._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": m._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": m._FACULTY_BY_SLUG.get(slug),
        "external_reviews": m._REVIEWS_BY_SLUG.get(slug),
        "content_sources": m._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(m.SCHOOLS) == 19
    assert len(m.PROGRAMS) >= 370
    assert len(set(m.PROGRAM_SLUGS)) == len(m.PROGRAM_SLUGS)
    assert m.RANKING_DATA["ownership_type"] == "public"
    assert "public research university" in m.DESCRIPTION.lower()
    assert "news.umich.edu/feed/" in m._INSTITUTION_CONTENT["news_rss"]
    from unipaith.data.profile_catalog_utils import validate_catalog

    assert not validate_catalog(m.PROGRAMS)


def test_coverable_programs_have_reviews():
    """Every coverable program must EITHER carry a gathered review OR explicitly
    record external_reviews as omitted in its _standard — never a silent blank,
    and never a synthesized review."""
    from scripts.fleet_audit import is_coverable

    missing = [
        spec["slug"]
        for spec in m.PROGRAMS
        if is_coverable(spec)
        and spec["slug"] not in m._REVIEWS_BY_SLUG
        and "external_reviews.summary"
        not in m._program_standard(spec["slug"], spec)["omitted"]
    ]
    assert not missing, f"Coverable programs with neither a review nor an omit: {missing[:10]}"


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(m._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"
    assert "school_outcomes.employed_or_continuing_ed" in m._OMITTED_INSTITUTION


def test_every_school_is_conformant():
    for spec in m.SCHOOLS:
        snap = _school_snapshot(spec)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{spec['name']} gaps: {bad}"
        assert snap["content_sources"].get("news_rss"), f"{spec['name']} missing news_rss"


def test_every_program_is_conformant_or_omitted():
    for spec in m.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(m._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"].get("news_rss"), f"{spec['slug']} missing news_rss"


def test_flagship_programs_carry_reviews():
    for slug in (
        "mich-master-of-business-administration-mba",
        "mich-juris-doctor-jd",
        "mich-business-ug",
        "mich-computer-science-ug-eng",
        "mich-doctor-of-medicine-md",
    ):
        assert slug in m._REVIEWS_BY_SLUG, f"{slug} should carry external_reviews"
        rev = m._REVIEWS_BY_SLUG[slug]
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]


def test_michigan_catalog_has_no_frame_stripped_shared_body():
    from unipaith.profile_standard.anti_stub import analyze, frame_stripped_shared_body

    report = analyze(m.PROGRAMS)
    assert report.is_clean, f"Michigan anti-stub regressed: {report.summary()}"
    shared = frame_stripped_shared_body(m.PROGRAMS, abs_chars=150)
    assert not shared, (
        f"Michigan credential siblings share a frame-stripped body on "
        f"{len(shared)} field(s): {shared[:8]}{' …' if len(shared) > 8 else ''}"
    )
