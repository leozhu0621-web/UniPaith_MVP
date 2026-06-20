"""The Emory profile conforms to the gold standard across institution, schools, and programs."""

from unipaith.data import emory_profile as p
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
    so = {**p.SCHOOL_OUTCOMES, "_standard": p._standard(p._OMITTED_INSTITUTION)}
    return {
        "description_text": p.DESCRIPTION,
        "student_body_size": p.UNDERGRAD_COUNT,
        "media_gallery": [p.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": p.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": p._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    spec = next(x for x in p.SCHOOLS if x["name"] == name)
    about = dict(p._ABOUT_DETAIL.get(name, {}))
    about["_standard"] = p._standard(p._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": spec["description"],
        "website_url": p._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": p._school_content(name),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    cost = (
        {
            "tuition_usd": p._TUITION_UG,
            "total_cost_of_attendance": p._UNDERGRAD_COA,
            "avg_net_price": p._AVG_NET_PRICE,
            "breakdown": {
                "tuition": p._TUITION_UG,
                "total_cost_of_attendance": p._UNDERGRAD_COA,
            },
            "funded": False,
            "source": p._COST_SRC[0],
            "source_url": p._COST_SRC[1],
        }
        if spec["degree_type"] == "bachelors"
        else {
            "note": "see program page",
            "source": "Emory University — program tuition page",
            "source_url": p._SCHOOL_WEBSITE.get(spec["school"]),
        }
    )
    outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug, spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": p._SCHOOL_WEBSITE.get(spec["school"]),
        "department": spec.get("department"),
        "tracks": p._TRACKS_BY_SLUG.get(slug),
        "application_requirements": p._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": p._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": p._FACULTY_BY_SLUG.get(slug),
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug),
        "content_sources": p._program_content(spec["school"], spec["keywords"]),
    }


def test_catalog_is_anti_stub_clean():
    from unipaith.profile_standard.anti_stub import analyze

    report = analyze(p.PROGRAMS)
    assert report.is_clean, f"anti-stub not clean: {report.summary()}"


def test_catalog_breadth_and_shape():
    assert len(p.SCHOOLS) == 9
    assert len(p.PROGRAMS) == 46
    assert len(set(p.PROGRAM_SLUGS)) == len(p.PROGRAM_SLUGS)
    assert p.RANKING_DATA["ownership_type"] == "private"
    assert "atlanta" in p.DESCRIPTION.lower()
    assert len(p.SCHOOL_OUTCOMES["campus_photos"]) >= 4
    assert p._INSTITUTION_CONTENT["news_rss"] == "https://www.trumba.com/calendars/emory-events.rss"
    assert p._INSTITUTION_CONTENT["events_feed"]["url"].endswith(".ics")


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(p._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for spec in p.SCHOOLS:
        snap = _school_snapshot(spec["name"])
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{spec['name']} gaps: {bad}"
        assert snap["content_sources"], f"{spec['name']} missing content_sources"
        assert snap["content_sources"].get("news_rss"), f"{spec['name']} missing news_rss"


def test_every_program_is_conformant_or_omitted():
    for spec in p.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(p._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_mba_has_reviews():
    assert p._FLAGSHIP in p._REVIEWS_BY_SLUG
    assert p._REVIEWS_BY_SLUG[p._FLAGSHIP]["sources"]
