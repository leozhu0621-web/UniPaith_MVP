"""The USC profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 21 real schools/academic units, and every one of
its 613 programs — mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``usc_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes when
it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import usc_profile as u
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
    so = {**u.SCHOOL_OUTCOMES, "_standard": u._standard(u._OMITTED_INSTITUTION)}
    return {
        "description_text": u.DESCRIPTION,
        "student_body_size": u.UNDERGRAD_COUNT,
        "media_gallery": [u.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": u.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": u._INSTITUTION_CONTENT,
    }


def _school_snapshot(m: dict) -> dict:
    about = {**u._about_for(m), "_standard": u._standard(u._about_omitted(m))}
    return {
        "name": m["name"],
        "description_text": u._school_description(m),
        "website_url": m["website"],
        "about_detail": about,
        "content_sources": u._school_content(m["name"]),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    is_ug = spec["degree_type"] == "bachelors"
    cost = u._undergrad_cost() if is_ug else u._grad_cost_fallback(spec)
    outcomes = dict(u._OUTCOMES_BY_SLUG.get(slug, {}))
    outcomes["_standard"] = u._program_standard(slug, spec)
    kw = u._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(u._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": u._website_for(spec),
        "department": spec.get("department"),
        "tracks": None,
        "application_requirements": u._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": u._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": u._FACULTY_BY_SLUG.get(slug),
        "external_reviews": u._REVIEWS_BY_SLUG.get(slug),
        "content_sources": u._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    # Full published degree catalog across Dornsife + 20 professional schools.
    assert len(u.SCHOOLS) == 21
    assert len(u.PROGRAMS) >= 600
    assert len(set(u.PROGRAM_SLUGS)) == len(u.PROGRAM_SLUGS)
    # online delivery is set on Bovard / online programs
    assert any(p["delivery_format"] == "online" for p in u.PROGRAMS)
    # ownership + classification drive the explore-card eyebrow
    assert u.RANKING_DATA["ownership_type"] == "private"
    assert "private" in u.DESCRIPTION.split(".")[0].lower()
    assert "private research university" in u.DESCRIPTION.lower()
    assert "today.usc.edu/feed/" in u._INSTITUTION_CONTENT["news_rss"]
    from unipaith.data.profile_catalog_utils import validate_catalog

    assert not validate_catalog(u.PROGRAMS)


def test_coverable_programs_have_reviews():
    """Every coverable program must EITHER carry a gathered review OR explicitly
    record external_reviews as omitted in its _standard — never a silent blank,
    and never a synthesized review."""
    from scripts.fleet_audit import is_coverable

    missing = [
        spec["slug"]
        for spec in u.PROGRAMS
        if is_coverable(spec)
        and spec["slug"] not in u._REVIEWS_BY_SLUG
        and "external_reviews.summary"
        not in u._program_standard(spec["slug"], spec)["omitted"]
    ]
    assert not missing, f"Coverable programs with neither a review nor an omit: {missing[:10]}"


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(u._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"
    assert "school_outcomes.employed_or_continuing_ed" in u._OMITTED_INSTITUTION


def test_every_school_is_conformant():
    for m in u._SCHOOL_META:
        snap = _school_snapshot(m)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{m['name']} gaps: {bad}"
        assert snap["content_sources"], f"{m['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in u.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(u._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_no_slug_prefixed_descriptions():
    """Kebab-case catalogue slugs must not leak into description_text (miss #8)."""
    import re

    slug_re = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s")
    leaks = [s["slug"] for s in u.PROGRAMS if slug_re.match(s.get("description") or "")]
    assert not leaks, f"slug-prefixed descriptions: {leaks[:5]}"


def test_no_field_echo_departments():
    """department must name USC's real school/college, not echo the field (miss #2)."""
    echo = [
        s["slug"]
        for s in u.PROGRAMS
        if s.get("department") == u._field_key(s["program_name"])
    ]
    assert not echo, f"field-echo departments: {echo[:5]}"
    # Beat the "1 reviewed program" bug: the coverable flagships carry external_reviews.
    for slug in (
        "usc-full-time-mba-program-mba",
        "usc-law-jd",
        "usc-medicine-md",
        "usc-computer-science-bs",
        "usc-computer-science-ms",
        "usc-cinematic-arts-film-and-television-production-bfa",
        "usc-journalism-ba",
        "usc-business-administration-bs",
        "usc-public-administration-mpa",
    ):
        assert slug in u._REVIEWS_BY_SLUG, f"{slug} should carry external_reviews"
        rev = u._REVIEWS_BY_SLUG[slug]
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]
    # MBA + JD also carry verified employment outcomes.
    for slug in ("usc-full-time-mba-program-mba", "usc-law-jd"):
        o = u._OUTCOMES_BY_SLUG[slug]
        assert o["employment_rate"] and o["conditions"] and o["source"]
