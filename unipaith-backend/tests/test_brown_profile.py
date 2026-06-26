"""The Brown profile conforms to the gold standard across institution, schools, and programs.

Adds the matcher-core + universal-depth gates (REPAIR_BACKLOG #1/#3/#4/#5): cip_code 100%,
who_its_for 100% and never a classification stub, every master's/professional tier carries a
published tuition (never the undergraduate sticker), and added reviews are program-specific
and sourced.
"""

import re

from unipaith.data import brown_profile as p
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


def _program_cost(spec: dict) -> dict:
    """Mirror apply()'s cost-resolution branch order."""
    slug = spec["slug"]
    cost_override = p._COST_BY_SLUG.get(slug)
    if cost_override is not None:
        return dict(cost_override)
    if spec["degree_type"] == "bachelors":
        return {
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
    return {
        "funded": spec["degree_type"] == "phd",
        "note": "see program page",
        "source": p._SFS_GRAD_SRC[0],
        "source_url": p._SFS_GRAD_SRC[1],
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug, spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": p._SCHOOL_WEBSITE.get(spec["school"]),
        "department": spec.get("department"),
        "tracks": p._TRACKS_BY_SLUG.get(slug),
        "application_requirements": p._requirements_for(spec),
        "cost_data": _program_cost(spec),
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
    assert len(p.SCHOOLS) == 7
    assert len(p.PROGRAMS) == 57
    assert len(set(p.PROGRAM_SLUGS)) == len(p.PROGRAM_SLUGS)
    assert p.RANKING_DATA["ownership_type"] == "private"
    assert "providence" in p.DESCRIPTION.lower()
    assert len(p.SCHOOL_OUTCOMES["campus_photos"]) >= 4
    assert p._INSTITUTION_CONTENT.get("news_rss")
    assert p._INSTITUTION_CONTENT.get("events_feed")


def test_no_duplicate_rendered_names():
    seen = set()
    for spec in p.PROGRAMS:
        key = (spec["program_name"], spec["degree_type"])
        assert key not in seen, f"duplicate rendered program: {key}"
        seen.add(key)


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


def test_cip_code_complete():
    """REPAIR_BACKLOG #1 — every program carries a real CIP join key for the matcher."""
    for spec in p.PROGRAMS:
        cip = p._CIP_BY_SLUG.get(spec["slug"])
        assert cip, f"{spec['slug']} missing cip_code"
        assert re.fullmatch(r"\d{2}\.\d{2,4}", cip), f"{spec['slug']} bad cip {cip}"
    assert set(p._CIP_BY_SLUG) == set(p.PROGRAM_SLUGS)


def test_who_its_for_complete_and_not_stub():
    """REPAIR_BACKLOG #4 — who_its_for is a universal depth field; 100%, never a stub."""
    assert set(p._WHO_BY_SLUG) == set(p.PROGRAM_SLUGS)
    for spec in p.PROGRAMS:
        who = p._WHO_BY_SLUG.get(spec["slug"])
        assert who and len(who) > 40, f"{spec['slug']} thin who_its_for"
        assert not who.lower().startswith("for students interested in"), spec["slug"]


def test_graduate_tiers_carry_published_tuition():
    """REPAIR_BACKLOG #3 — master's/professional tiers must not be matcher-blind on budget."""
    for spec in p.PROGRAMS:
        dtype = spec["degree_type"]
        if dtype in ("masters", "professional"):
            assert p._grad_has_verified_tuition(spec), spec["slug"]
            cost = p._COST_BY_SLUG.get(spec["slug"])
            assert cost is not None and cost.get("tuition_usd"), spec["slug"]
            # never the undergraduate sticker copied down onto a graduate row
            assert cost["tuition_usd"] != p._TUITION_UG, spec["slug"]
        elif dtype == "phd":
            # doctoral rows are funded omit-with-reason, not a stamped flat tuition
            assert not p._grad_has_verified_tuition(spec), spec["slug"]


def test_reviews_are_program_specific_and_sourced():
    """Added reviews carry resolvable sources and no CIP-rollup synthesis tells."""
    assert len(p._REVIEWS_BY_SLUG) >= 4
    for slug, rev in p._REVIEWS_BY_SLUG.items():
        assert rev["summary"] and rev["sources"], slug
        assert all(s.get("url", "").startswith("http") for s in rev["sources"]), slug
        assert ", General" not in rev["summary"] and ", Other" not in rev["summary"], slug
        assert rev.get("disclaimer"), slug
