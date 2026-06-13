"""The Northwestern University profile conforms to the gold standard across every node it
models — the institution, eleven schools, and their full published degree catalog —
mirroring the MIT/Sloan/MBAn and Yale/Columbia reference certifications.

Pure (no DB): builds each node's persisted snapshot from the northwestern_profile module
(mirroring the columns ``apply()`` writes) and runs ``check_conformance``. The only gaps
permitted are the fields each node honestly records in its ``_standard.omitted`` list;
``tracks`` and ``insights`` are whole-section omittable for catalog programs (only the
deeply-enriched flagship carries them). The McCormick B.S. in Computer Science is the
deeply-enriched flagship.
"""

from unipaith.data import northwestern_profile as n
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

_FLAGSHIP = "northwestern-computer-science-bs"
_OMITTABLE_SECTIONS = {"tracks", "insights"}


def _institution_snapshot() -> dict:
    so = {**n.SCHOOL_OUTCOMES, "_standard": n._standard(n._OMITTED_INSTITUTION)}
    for path in n._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            rest = path.split(".", 1)[1]
            if "." not in rest:
                so.pop(rest, None)
    return {
        "description_text": n.DESCRIPTION,
        "student_body_size": n.UNDERGRAD_COUNT,
        "media_gallery": [n._CAMPUS_PHOTO],
        "ranking_data": n.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": n._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = n._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = n._standard(n._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in n.SCHOOLS if s["name"] == name),
        "website_url": n._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": n._school_content(name),
    }


def _cost_for(spec: dict) -> dict:
    slug = spec["slug"]
    if slug in n._COST_BY_SLUG:
        return dict(n._COST_BY_SLUG[slug])
    if n._has_undergrad_rate(spec):
        return {"tuition_usd": n._TUITION_UG, "source": "NCES College Navigator (UNITID 147767)"}
    return {"note": "varies", "source": "Northwestern University — program tuition pages"}


def _outcomes_for(slug: str) -> dict:
    fos = n._FOS_OUTCOMES.get(slug)
    if fos is not None:
        out = {
            "median_salary": fos[0],
            "scope": "program",
            "conditions": n._FOS_CONDITIONS,
            "source": "U.S. Dept. of Education College Scorecard — Field of Study",
        }
    else:
        out = dict(n._OUTCOMES_INSTITUTION)
    out["_standard"] = n._program_standard(slug)
    return out


def _program_snapshot(slug: str) -> dict:
    spec = n._SPEC_BY_SLUG[slug]
    kw = n._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
        n._SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
    )
    return {
        "program_name": n._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": n._WEBSITE_BY_SLUG.get(slug) or n._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": n._TRACKS_BY_SLUG.get(slug),
        "application_requirements": n._requirements_for(spec),
        "cost_data": _cost_for(spec),
        "outcomes_data": _outcomes_for(slug),
        "class_profile": n._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": n._FACULTY_BY_SLUG.get(slug),
        "external_reviews": n._REVIEWS_BY_SLUG.get(slug),
        "content_sources": n._program_content(spec["school"], kw),
    }


def test_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(n._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections


def test_eleven_schools_each_gold_except_recorded_omissions():
    assert len(n.SCHOOLS) == 11
    names = {s["name"] for s in n.SCHOOLS}
    assert names == set(n._SCHOOL_WEBSITE)
    for name in names:
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(n._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, f"{name} missing sections: {res.missing_sections}"
        assert n._school_content(name)["news_rss"], f"{name} has no news feed"


def test_every_school_and_program_has_a_working_feed():
    for s in n.SCHOOLS:
        cs = n._school_content(s["name"])
        assert cs["news_rss"].startswith("https://")
        assert cs["events_feed"]["url"].endswith(".ics") or "ical" in cs["events_feed"]["url"]
    for spec in n.PROGRAMS:
        kw = n._PROGRAM_KEYWORDS_BY_SLUG.get(spec["slug"]) or list(
            n._SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
        )
        cs = n._program_content(spec["school"], kw)
        assert cs["news_rss"] and cs["events_feed"]["url"]


def test_flagship_is_deeply_enriched():
    assert _FLAGSHIP in n._TRACKS_BY_SLUG
    assert _FLAGSHIP in n._FACULTY_BY_SLUG
    assert _FLAGSHIP in n._REVIEWS_BY_SLUG
    res = check_conformance(
        "program", _program_snapshot(_FLAGSHIP), profile_version=STANDARD_VERSION
    )
    assert not res.missing_sections, f"flagship missing sections: {res.missing_sections}"
    assert set(res.missing_fields) <= set(n._program_standard(_FLAGSHIP)["omitted"]), (
        f"flagship unexpected field gaps: {res.missing_fields}"
    )


def test_full_catalog_breadth_and_online_coverage():
    assert len(n.PROGRAMS) >= 200, f"catalog too short: {len(n.PROGRAMS)}"
    assert len(n.PROGRAM_SLUGS) == len(set(n.PROGRAM_SLUGS)), "duplicate program slug"
    formats = {p["delivery_format"] for p in n.PROGRAMS}
    assert "online" in formats, "no online programs in catalog"
    for spec in n.PROGRAMS:
        assert spec.get("delivery_format") in {"in_person", "online", "hybrid"}, spec["slug"]


def test_every_program_is_gold_except_recorded_omissions():
    unit_names = {s["name"] for s in n.SCHOOLS}
    for spec in n.PROGRAMS:
        slug = spec["slug"]
        assert spec["school"] in unit_names, f"{slug} maps to unknown unit"
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        allowed = set(n._program_standard(slug)["omitted"])
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        assert set(res.missing_sections) <= _OMITTABLE_SECTIONS, (
            f"{slug} unexpected missing sections: {res.missing_sections}"
        )
