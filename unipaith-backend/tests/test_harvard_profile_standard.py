"""The Harvard profile conforms to the gold standard across its whole tree — the
institution, all twelve schools, and the full IPEDS breadth-first program catalog.

Pure (no DB): builds each node's persisted snapshot from the harvard_profile module and
runs ``check_conformance``. A node is accepted only when it is gold OR every remaining
required field is recorded in that node's ``_standard.omitted`` (verified-unavailable)
with a real reason.
"""

from unipaith.data import harvard_profile as h
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "harvard-mba"


def _institution_snapshot() -> dict:
    school_outcomes = {**h.SCHOOL_OUTCOMES}
    for path in h._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            school_outcomes.pop(path.split(".", 1)[1], None)
    school_outcomes["_standard"] = h._standard(h._OMITTED_INSTITUTION)
    return {
        "description_text": h.DESCRIPTION,
        "student_body_size": h.UNDERGRAD_COUNT,
        "media_gallery": [h._CAMPUS_PHOTO],
        "ranking_data": h.RANKING_DATA,
        "school_outcomes": school_outcomes,
        "content_sources": h._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = h._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = h._standard(h._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in h.SCHOOLS if s["name"] == name),
        "website_url": h._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": h._school_content(name),
    }


def _program_cost(spec: dict) -> dict:
    slug = spec["slug"]
    if slug in h._TUITION_BY_SLUG:
        return {"tuition_usd": h._TUITION_BY_SLUG[slug], "source": "x"}
    if spec["degree_type"] == "phd":
        return {"tuition_usd": 0, "source": "x"}
    if (
        slug == "harvard-alm"
        or spec.get("delivery_format") == "online"
        or spec["degree_type"] == "certificate"
    ):
        return {}
    if spec["degree_type"] == "bachelors":
        return {"tuition_usd": h._TUITION_UNDERGRAD, "source": "x"}
    return {}


def _program_outcomes(spec: dict) -> dict:
    slug = spec["slug"]
    out_override = h._OUTCOMES_BY_SLUG.get(slug)
    fos = h._FOS_OUTCOMES.get(slug)
    if out_override is not None:
        outcomes = dict(out_override)
    elif fos is not None:
        salary, debt, cip = fos
        outcomes = {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "source": "U.S. Dept. of Education College Scorecard — Field of Study",
        }
        if debt is not None:
            outcomes["median_debt_completers"] = debt
    elif spec["degree_type"] in ("bachelors", "masters", "phd"):
        outcomes = dict(h._OUTCOMES_INSTITUTION)
    else:
        outcomes = None
    if outcomes is None:
        return {"_standard": h._program_standard(spec)}
    outcomes["_standard"] = h._program_standard(spec)
    return outcomes


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    reqs = dict(h._requirements_for(spec))
    deadlines = h._DEADLINES_BY_SLUG.get(slug)
    if deadlines is not None:
        reqs["deadlines"] = deadlines
    return {
        "program_name": h._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": h._DESC_RICH_BY_SLUG.get(slug) or spec["description"],
        "website_url": h._WEBSITE_BY_SLUG.get(slug) or h._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": h._HL_BY_SLUG.get(slug) or h._HL_BY_TYPE.get(spec["degree_type"]),
        "who_its_for": h._WHO_BY_SLUG.get(slug) or h._WHO_BY_TYPE.get(spec["degree_type"]),
        "tracks": h._TRACKS_BY_SLUG.get(slug),
        "application_requirements": reqs,
        "cost_data": _program_cost(spec),
        "outcomes_data": _program_outcomes(spec),
        "class_profile": h._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": h._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": h._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": h._MBA_CONTENT if slug == _FLAGSHIP else h._program_content(spec),
    }


def _section_gaps_unexpected(level: str, missing_sections: list[str], omitted: set[str]) -> list:
    bad = []
    for secid in missing_sections:
        sec = next(s for s in MANIFEST[level] if s.id == secid)
        req = {f.path for f in sec.fields if f.enrich and f.required}
        if not req <= omitted:
            bad.append(secid)
    return bad


def test_harvard_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    omitted = set(h._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)
    assert h.SCHOOL_OUTCOMES.get("media_credit")
    assert h.DESCRIPTION.startswith(
        "Harvard University is a private research university in Cambridge, MA"
    )


def test_all_twelve_schools_done():
    assert len(h.SCHOOLS) == 12
    assert {s["name"] for s in h.SCHOOLS} == set(h._SCHOOL_WEBSITE)
    for school in h.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(h._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name


def test_full_catalog_breadth():
    assert len(h.PROGRAMS) >= 280, f"catalog too short: {len(h.PROGRAMS)}"
    assert len(h.PROGRAM_SLUGS) == len(set(h.PROGRAM_SLUGS)), "duplicate program slug"
    for spec in h.PROGRAMS:
        fmt = spec.get("delivery_format", "in_person")
        assert fmt in {"in_person", "online", "hybrid"}, spec["slug"]


def test_catalog_has_no_padding_stubs():
    """Catalog must not carry bare-abbr / CIP×award-level padding stubs."""
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(h.PROGRAMS)
    assert not errors, f"Catalog padding detected: {errors}"


def test_institution_has_campus_photo_gallery():
    photos = h.SCHOOL_OUTCOMES.get("campus_photos") or []
    assert len(photos) >= 4, "institution needs a verified 4–5 photo gallery"
    for photo in photos:
        assert photo.get("url") and photo.get("credit"), photo


def test_every_program_is_done():
    for spec in h.PROGRAMS:
        res = check_conformance(
            "program", _program_snapshot(spec), profile_version=STANDARD_VERSION
        )
        omitted = set(h._program_standard(spec)["omitted"])
        assert set(res.missing_fields) <= omitted, (
            f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        )
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), (
            spec["slug"]
        )


def test_flagship_mba_is_deeply_enriched():
    spec = next(p for p in h.PROGRAMS if p["slug"] == _FLAGSHIP)
    res = check_conformance(
        "program", _program_snapshot(spec), profile_version=STANDARD_VERSION
    )
    omitted = set(h._program_standard(spec)["omitted"])
    assert "harvard-mba" in h._REVIEWS_BY_SLUG
    assert "harvard-mba" in h._TRACKS_BY_SLUG
    assert set(res.missing_fields) <= omitted
    assert not _section_gaps_unexpected("program", res.missing_sections, omitted)


def test_every_node_has_content_sources():
    assert h._INSTITUTION_CONTENT.get("news_rss")
    for school in h.SCHOOLS:
        cs = h._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed"), school["name"]
    for spec in h.PROGRAMS:
        cs = h._MBA_CONTENT if spec["slug"] == _FLAGSHIP else h._program_content(spec)
        assert cs.get("news_rss") and cs.get("keywords"), spec["slug"]
