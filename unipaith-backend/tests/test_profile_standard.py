"""Phase 1 — the profile standard certifies the MIT/Sloan/MBAn reference instance
as 100% conformant and detects gaps on anything else."""

from unipaith.data import mit_profile as mit
from unipaith.profile_standard import STANDARD_VERSION, check_conformance


def test_empty_program_is_non_conformant():
    res = check_conformance("program", {})
    assert res.conformant is False
    assert "basics" in res.missing_sections


def test_stale_version_flags_non_conformant():
    # A snapshot that satisfies the fields but carries an older version is stale.
    res = check_conformance("program", _program_snapshot("mit-sloan-mban"), profile_version=0)
    assert res.stale is True
    assert res.conformant is False


def _program_snapshot(slug: str) -> dict:
    """Build the program's persisted shape from the MIT module, mirroring the
    column names _apply_programs writes (faculty_contacts / external_reviews /
    tracks / content_sources)."""
    spec = next(p for p in mit.PROGRAMS if p["slug"] == slug)
    return {
        "program_name": mit._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": mit._DESC_RICH_BY_SLUG.get(slug) or spec["description"],
        "website_url": mit._WEBSITE_BY_SLUG.get(slug),
        "highlights": mit._HL_BY_SLUG.get(slug) or mit._HL_BY_TYPE.get(spec["degree_type"]),
        "who_its_for": mit._WHO_BY_SLUG.get(slug) or mit._WHO_BY_TYPE.get(spec["degree_type"]),
        "tracks": mit._TRACKS_BY_SLUG.get(slug),
        "application_requirements": mit._REQ_BY_SLUG.get(slug, mit._REQ_MBA),
        "cost_data": mit._COST_BY_SLUG.get(slug, {}),
        "outcomes_data": mit._OUTCOMES_BY_SLUG.get(slug, {}),
        "class_profile": mit._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": mit._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": mit._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": mit._MBAN_CONTENT,
    }


def test_mban_program_is_conformant():
    res = check_conformance(
        "program", _program_snapshot("mit-sloan-mban"), profile_version=STANDARD_VERSION
    )
    assert res.conformant, (
        f"MBAn is the gold standard; gaps: {res.missing_fields} {res.missing_sections}"
    )


def test_sloan_school_is_conformant():
    sloan = next(s for s in mit.SCHOOLS if "Sloan" in s["name"])
    snap = {
        "name": sloan["name"],
        "description_text": sloan.get("description", ""),
        "website_url": mit._SCHOOL_WEBSITE.get(sloan["name"]),
        "about_detail": mit._SLOAN_ABOUT_DETAIL,
        "content_sources": mit._SLOAN_CONTENT,
    }
    res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
    assert res.conformant, f"Sloan gaps: {res.missing_fields} {res.missing_sections}"


def test_mit_institution_is_conformant():
    snap = {
        "description_text": mit.DESCRIPTION,
        "student_body_size": mit.UNDERGRAD_COUNT,
        "media_gallery": [mit._CAMPUS_PHOTO],
        "ranking_data": mit.RANKING_DATA,
        "school_outcomes": mit.SCHOOL_OUTCOMES,
        "content_sources": {"news_rss": "x", "events_feed": {}, "social": {}},
    }
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    assert res.conformant, f"MIT gaps: {res.missing_fields} {res.missing_sections}"
