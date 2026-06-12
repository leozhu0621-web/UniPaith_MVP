"""The Yale University profile (the completed tree) conforms to the gold standard across
every node it models — the institution, fifteen schools, and their full published degree
catalog — mirroring the MIT/Sloan/MBAn and Columbia/Chicago reference certifications.

Pure (no DB): builds each node's persisted snapshot from the yale_profile module (mirroring
the columns ``apply()`` writes) and runs ``check_conformance``. The only gaps permitted are
the fields each node honestly records in its ``_standard.omitted`` list; ``tracks`` and
``insights`` are whole-section omittable for catalog programs (only the deeply-enriched
flagship carries them). Computer Science is the deeply-enriched flagship.
"""

from unipaith.data import yale_profile as y
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

_FLAGSHIP = "yale-computer-science-bs"
_OMITTABLE_SECTIONS = {"tracks", "insights"}


def _institution_snapshot() -> dict:
    return {
        "description_text": y.DESCRIPTION,
        "student_body_size": y.UNDERGRAD_COUNT,
        "media_gallery": [y._CAMPUS_PHOTO],
        "ranking_data": y.RANKING_DATA,
        "school_outcomes": {**y.SCHOOL_OUTCOMES, "_standard": y._standard(y._OMITTED_INSTITUTION)},
        "content_sources": y._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = y._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = y._standard(y._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in y.SCHOOLS if s["name"] == name),
        "website_url": y._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": y._school_content(name),
    }


def _cost_for(slug: str, spec: dict) -> dict:
    """Mirror the cost branch of _apply_programs (conformance reads tuition_usd + source)."""
    if slug in y._COST_BY_SLUG:
        return dict(y._COST_BY_SLUG[slug])
    if spec["degree_type"] == "bachelors":
        return {"tuition_usd": y._TUITION_UG, "source": "Yale Student Accounts"}
    return {"note": "varies", "source": "Yale University Catalog — Tuition & Fees"}


def _outcomes_for(slug: str) -> dict:
    fos = y._FOS_OUTCOMES.get(slug)
    if fos is not None:
        out = {
            "median_salary": fos[0],
            "scope": "program",
            "conditions": y._FOS_CONDITIONS,
            "source": "U.S. Dept. of Education College Scorecard — Field of Study",
        }
    else:
        out = dict(y._OUTCOMES_INSTITUTION)
    out["_standard"] = y._program_standard(slug)
    return out


def _program_snapshot(slug: str) -> dict:
    """Mirror the columns _apply_programs writes for a program slug."""
    spec = y._SPEC_BY_SLUG[slug]
    kw = y._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
        y._SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
    )
    return {
        "program_name": y._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": y._WEBSITE_BY_SLUG.get(slug) or y._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": y._TRACKS_BY_SLUG.get(slug),
        "application_requirements": y._requirements_for(spec),
        "cost_data": _cost_for(slug, spec),
        "outcomes_data": _outcomes_for(slug),
        "class_profile": y._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": y._FACULTY_BY_SLUG.get(slug),
        "external_reviews": y._REVIEWS_BY_SLUG.get(slug),
        "content_sources": y._program_content(spec["school"], kw),
    }


def test_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(y._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections


def test_fifteen_schools_each_gold_except_recorded_omissions():
    assert len(y.SCHOOLS) == 15
    names = {s["name"] for s in y.SCHOOLS}
    assert names == set(y._SCHOOL_WEBSITE)
    for name in names:
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(y._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, f"{name} missing sections: {res.missing_sections}"
        assert y._school_content(name)["news_rss"], f"{name} has no news feed"


def test_every_school_and_program_has_a_working_feed():
    # The empty-Events-&-Updates bug: every school and program must carry a real news_rss
    # + events_feed so the daily ingest has something to fetch.
    for s in y.SCHOOLS:
        cs = y._school_content(s["name"])
        assert cs["news_rss"].startswith("https://news.yale.edu")
        assert cs["events_feed"]["url"].endswith(".ics")
    for spec in y.PROGRAMS:
        kw = y._PROGRAM_KEYWORDS_BY_SLUG.get(spec["slug"]) or spec.get("keywords")
        kw = kw or list(y._SCHOOL_FEED_SPEC[spec["school"]]["keywords"])
        cs = y._program_content(spec["school"], kw)
        assert cs["news_rss"] and cs["events_feed"]["url"]


def test_flagship_is_deeply_enriched():
    assert _FLAGSHIP in y._TRACKS_BY_SLUG
    assert _FLAGSHIP in y._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in y._FACULTY_BY_SLUG
    assert _FLAGSHIP in y._REVIEWS_BY_SLUG
    res = check_conformance(
        "program", _program_snapshot(_FLAGSHIP), profile_version=STANDARD_VERSION
    )
    # The flagship carries tracks + insights (no omittable sections); the only permitted
    # field gaps are Yale's universally-omitted per-program employment_rate / top_industries
    # (Yale reports first-destination outcomes college-wide, not per program).
    assert not res.missing_sections, f"flagship missing sections: {res.missing_sections}"
    assert set(res.missing_fields) <= set(y._program_standard(_FLAGSHIP)["omitted"]), (
        f"flagship unexpected field gaps: {res.missing_fields}"
    )


def test_coverable_programs_have_external_reviews():
    """Coverable programs (MBA, JD, MPH, MArch, MEM, flagship majors) must carry reviews."""
    coverable = [
        _FLAGSHIP,
        "yale-mba",
        "yale-economics-bs",
        "yale-public-health-mph",
        "yale-juris-doctor-jd-prof",
        "yale-architecture-march",
        "yale-environmental-management-mem",
    ]
    for slug in coverable:
        assert slug in y._REVIEWS_BY_SLUG, slug
        assert y._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(y._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_institution_has_media_credit():
    assert y.SCHOOL_OUTCOMES.get("media_credit"), "campus photo must carry attribution"


def test_description_leads_with_research_university():
    assert y.DESCRIPTION.startswith(
        "Yale University is a private research university in New Haven, CT"
    )


def test_full_catalog_breadth():
    # The short-catalog bug: Yale offers far more than the original 20. The set must be the
    # real published catalog (Yale College majors + every school's graduate/professional
    # degrees + GSAS programs), cross-checked against the catalog pages.
    assert len(y.PROGRAMS) >= 180, f"catalog too short: {len(y.PROGRAMS)}"
    assert len(y.PROGRAM_SLUGS) == len(set(y.PROGRAM_SLUGS)), "duplicate program slug"
    for spec in y.PROGRAMS:
        assert spec.get("delivery_format") in {"in_person", "online", "hybrid"}, spec["slug"]


def test_every_program_is_gold_except_recorded_omissions():
    unit_names = {s["name"] for s in y.SCHOOLS}
    for spec in y.PROGRAMS:
        slug = spec["slug"]
        assert spec["school"] in unit_names, f"{slug} maps to unknown unit"
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        allowed = set(y._program_standard(slug)["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        assert set(res.missing_sections) <= _OMITTABLE_SECTIONS, (
            f"{slug} unexpected missing sections: {res.missing_sections}"
        )
