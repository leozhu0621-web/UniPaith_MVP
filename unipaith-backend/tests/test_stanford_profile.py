"""The Stanford profile conforms to the gold standard for its certified trio —
the institution, the Graduate School of Business, and the flagship MBA program —
mirroring the MIT/Sloan/MBAn reference certification in test_profile_standard.

Pure (no DB): builds each node's persisted snapshot from the stanford_profile
module and runs ``check_conformance``. The only institution-level gap permitted is
the field Stanford does not publish and that the module honestly records in its
``_standard.omitted`` list.
"""

from unipaith.data import stanford_profile as sf
from unipaith.profile_standard import STANDARD_VERSION, check_conformance


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = next(p for p in sf.PROGRAMS if p["slug"] == slug)
    out_override = sf._OUTCOMES_BY_SLUG.get(slug)
    fos = sf._FOS_OUTCOMES.get(slug)
    if out_override is not None:
        outcomes = dict(out_override)
    elif fos is not None:
        salary, cip = fos
        outcomes = {"median_salary": salary, "scope": "program", "cip": cip, "source": "x"}
    else:
        outcomes = dict(sf._OUTCOMES_INSTITUTION)
    if slug == "stanford-mba":
        cost = sf._COST_BY_SLUG[slug]
    elif spec["degree_type"] == "phd":
        cost = {"tuition_usd": 0, "source": "x"}
    else:
        cost = sf._COST_BY_SLUG.get(slug, {"tuition_usd": 65910, "source": "x"})
    if slug == "stanford-mba":
        req = sf._REQ_MBA
    elif spec["degree_type"] == "professional":
        req = sf._REQ_PROFESSIONAL
    elif spec["degree_type"] == "bachelors":
        req = sf._REQ_UNDERGRAD
    else:
        req = sf._REQ_GRAD
    return {
        "program_name": sf._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": sf._WEBSITE_BY_SLUG.get(slug),
        "highlights": sf._HL_BY_SLUG.get(slug) or sf._HL_BY_TYPE.get(spec["degree_type"]),
        "who_its_for": sf._WHO_BY_SLUG.get(slug) or sf._WHO_BY_TYPE.get(spec["degree_type"]),
        "tracks": sf._TRACKS_BY_SLUG.get(slug),
        "application_requirements": req,
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": sf._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": sf._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": sf._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": sf._MBA_CONTENT if slug == "stanford-mba" else None,
    }


def _school_snapshot(name: str) -> dict:
    return {
        "name": name,
        "description_text": next(s["description"] for s in sf.SCHOOLS if s["name"] == name),
        "website_url": sf._SCHOOL_WEBSITE.get(name),
        "about_detail": sf._ABOUT_DETAIL.get(name),
        "content_sources": sf._GSB_CONTENT if name == sf._GSB else None,
    }


def _institution_snapshot() -> dict:
    return {
        "description_text": sf.DESCRIPTION,
        "student_body_size": sf.UNDERGRAD_COUNT,
        "media_gallery": [sf._CAMPUS_PHOTO],
        "ranking_data": sf.RANKING_DATA,
        "school_outcomes": sf.SCHOOL_OUTCOMES,
        "content_sources": sf._INSTITUTION_CONTENT,
    }


def test_stanford_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    # The only permitted gaps are the fields the module honestly omits.
    assert set(res.missing_fields) <= set(sf._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections
    assert "school_outcomes.employed_or_continuing_ed" in sf._OMITTED_INSTITUTION


def test_stanford_gsb_school_is_conformant():
    res = check_conformance("school", _school_snapshot(sf._GSB), profile_version=STANDARD_VERSION)
    assert res.conformant, f"GSB gaps: {res.missing_fields} {res.missing_sections}"


def test_stanford_mba_program_is_conformant():
    res = check_conformance(
        "program", _program_snapshot("stanford-mba"), profile_version=STANDARD_VERSION
    )
    assert res.conformant, f"MBA gaps: {res.missing_fields} {res.missing_sections}"


def test_all_seven_schools_have_about_detail():
    assert {s["name"] for s in sf.SCHOOLS} == set(sf._SCHOOL_WEBSITE)
    for school in sf.SCHOOLS:
        assert sf._ABOUT_DETAIL.get(school["name"]), f"{school['name']} missing about_detail"


def test_every_program_maps_to_a_real_school():
    school_names = {s["name"] for s in sf.SCHOOLS}
    for spec in sf.PROGRAMS:
        assert spec["school"] in school_names, f"{spec['slug']} maps to unknown school"
    assert len(sf.PROGRAM_SLUGS) == len(set(sf.PROGRAM_SLUGS)), "duplicate program slug"


def test_depth_reviews_not_merged():
    """Synthesized DEPTH_REVIEWS must not ship on CIP-rollup catalog rows (miss #8)."""
    assert (
        "stanford-aerospace-aeronautical-and-astronautical-space-engineering-bs"
        not in sf._REVIEWS_BY_SLUG
    )
    assert len(sf._REVIEWS_BY_SLUG) <= 15


def test_no_synthesized_review_theme_reuse():
    from collections import Counter

    reviewed = {s: r for s, r in sf._REVIEWS_BY_SLUG.items() if s in sf.PROGRAM_SLUGS}
    theme_ct: Counter = Counter()
    for r in reviewed.values():
        for detail in {t["detail"] for t in r.get("themes", [])}:
            theme_ct[detail] += 1
    reused = {d: c for d, c in theme_ct.items() if c >= 3}
    assert not reused, f"theme detail reused across >=3 programs: {list(reused)[:3]}"
