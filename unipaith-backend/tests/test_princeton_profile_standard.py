"""The Princeton profile conforms to the gold standard across its whole tree — the
institution, every academic unit, and its FULL published degree catalog — mirroring the
MIT/Sloan/MBAn, Yale and Carnegie Mellon reference certifications.

Pure (no DB): builds each node's persisted snapshot from the princeton_profile module
(mirroring the columns ``apply()`` writes) and runs ``check_conformance``. The only gaps
permitted are the fields each node honestly records in its ``_standard.omitted`` list.
Every school AND every program carries a real ``content_sources`` feed (the empty
Events & Updates bug must never recur), and the catalog is the real Princeton catalog —
all 37 undergraduate concentrations plus every degree-granting Graduate School field.
Computer Science is the deeply-enriched flagship.
"""

from unipaith.data import princeton_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

_FLAGSHIP = "princeton-computer-science-bs"
_OMITTABLE_SECTIONS = {"tracks", "insights"}


def _institution_snapshot() -> dict:
    school_outcomes = {**p.SCHOOL_OUTCOMES}
    for path in p._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            school_outcomes.pop(path.split(".", 1)[1], None)
    school_outcomes["_standard"] = p._standard(p._OMITTED_INSTITUTION)
    return {
        "description_text": p.DESCRIPTION,
        "student_body_size": p.UNDERGRAD_COUNT,
        "media_gallery": [p._CAMPUS_PHOTO],
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
    fos = p._FOS_OUTCOMES.get(slug)
    if fos is not None:
        salary, cip = fos
        outcomes = {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "conditions": p._FOS_CONDITIONS,
            "source": "x",
        }
    else:
        outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug)
    kw = p._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(p._SCHOOL_FEED_SPEC[spec["school"]])
    return {
        "program_name": p._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": p._WEBSITE_BY_SLUG.get(slug),
        "highlights": p._HL_BY_SLUG.get(slug) or p._HL_BASELINE,
        "who_its_for": p._WHO_BY_SLUG.get(slug) or p._WHO_BASELINE,
        "tracks": p._TRACKS_BY_SLUG.get(slug),
        "application_requirements": p._requirements_for(spec),
        "cost_data": p._cost_for(spec),
        "outcomes_data": outcomes,
        "class_profile": p._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": p._FACULTY_BY_SLUG.get(slug),
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug),
        "content_sources": p._program_content(spec["school"], kw),
    }


def test_princeton_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(p._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections
    assert "school_outcomes.employed_or_continuing_ed" in p._OMITTED_INSTITUTION
    # The institution feed must carry a real, fetchable news RSS (so Updates populate).
    assert p._INSTITUTION_CONTENT["news_rss"].startswith("https://www.princeton.edu/news")


def test_five_units_each_gold_except_recorded_omissions():
    assert {s["name"] for s in p.SCHOOLS} == set(p._SCHOOL_WEBSITE)
    for school in p.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(p._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, f"{name} missing sections: {res.missing_sections}"
        assert p._ABOUT_DETAIL.get(name), f"{name} missing about_detail"


def test_every_school_and_program_has_a_working_feed():
    # The empty-Events-&-Updates bug: every school and program must carry a real news_rss
    # so the daily ingest has something to fetch (Princeton exposes no public events iCal,
    # so events_feed is honestly omitted — Updates still populate from the news RSS).
    for s in p.SCHOOLS:
        cs = p._school_content(s["name"])
        assert cs["news_rss"].startswith("https://www.princeton.edu/news")
        assert cs["keywords"], f"{s['name']} has no feed keywords"
    for spec in p.PROGRAMS:
        kw = p._PROGRAM_KEYWORDS_BY_SLUG.get(spec["slug"]) or list(
            p._SCHOOL_FEED_SPEC[spec["school"]]
        )
        cs = p._program_content(spec["school"], kw)
        assert cs["news_rss"] and cs["keywords"], f"{spec['slug']} has no working feed"


def test_flagship_is_deeply_enriched():
    assert _FLAGSHIP in p._TRACKS_BY_SLUG
    assert _FLAGSHIP in p._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in p._FACULTY_BY_SLUG
    assert _FLAGSHIP in p._REVIEWS_BY_SLUG
    res = check_conformance(
        "program", _program_snapshot(_FLAGSHIP), profile_version=STANDARD_VERSION
    )
    assert not res.missing_sections, f"flagship missing sections: {res.missing_sections}"
    assert set(res.missing_fields) <= set(p._program_standard(_FLAGSHIP)["omitted"]), (
        f"flagship unexpected gaps: {res.missing_fields}"
    )


def test_full_catalog_breadth():
    # The short-catalog bug: Princeton offers far more than the original 22. The set must
    # be the real published catalog — all 37 undergraduate concentrations plus every
    # degree-granting Graduate School field (Ph.D. + professional master's).
    assert len(p.PROGRAMS) >= 85, f"catalog too short: {len(p.PROGRAMS)}"
    assert len(p.PROGRAM_SLUGS) == len(set(p.PROGRAM_SLUGS)), "duplicate program slug"
    ug = [s for s in p.PROGRAMS if s["degree_type"] == "bachelors"]
    assert len(ug) == 37, f"expected 37 undergraduate concentrations, got {len(ug)}"
    grad = [s for s in p.PROGRAMS if s["degree_type"] in {"masters", "phd"}]
    assert len(grad) >= 45, f"graduate catalog too short: {len(grad)}"
    for spec in p.PROGRAMS:
        assert spec.get("delivery_format") in {"in_person", "online", "hybrid"}, spec["slug"]


def test_every_program_is_gold_except_recorded_omissions():
    unit_names = {s["name"] for s in p.SCHOOLS}
    for spec in p.PROGRAMS:
        slug = spec["slug"]
        assert spec["school"] in unit_names, f"{slug} maps to unknown unit"
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        allowed = set(p._program_standard(slug)["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        assert set(res.missing_sections) <= _OMITTABLE_SECTIONS, (
            f"{slug} unexpected section gaps: {res.missing_sections}"
        )
