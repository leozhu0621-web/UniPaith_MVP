"""The UC Irvine profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 15 real schools, and every one of its programs — mirroring
the MIT/Sloan reference certification (enrich-profile §8.5).

Pure (no DB): builds each node's persisted snapshot from the ``uci_profile`` module exactly
as ``apply()`` writes it, and runs ``check_conformance``. A node passes when it is gold OR
every remaining required gap is recorded in that node's ``_standard.omitted``.
"""

from unipaith.data import uci_profile as u
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_COVERABLE_REVIEWS = {"uci-jd", "uci-mba-full-time", "uci-md"}


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
        "media_gallery": [u._EXTRA_CAMPUS_PHOTOS[0]["url"]],
        "ranking_data": u.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": u._INSTITUTION_CONTENT,
    }


def _school_snapshot(spec: dict) -> dict:
    about = {**u._ABOUT_DETAIL.get(spec["name"], {}),
             "_standard": u._standard(u._ABOUT_OMITTED.get(spec["name"], []))}
    return {
        "name": spec["name"],
        "description_text": spec["description"],
        "website_url": u._SCHOOL_WEBSITE.get(spec["name"]),
        "about_detail": about,
        "content_sources": u._school_content(spec["name"]),
    }


def _cost_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return u._undergrad_cost()
    if spec.get("tuition") is not None:
        return {
            "tuition_usd": spec["tuition"], "funded": False, "note": spec.get("cost_note", ""),
            "source": (spec.get("cost_source") or u._GRAD_COST_SRC)[0],
            "source_url": (spec.get("cost_source") or u._GRAD_COST_SRC)[1], "year": "2025-26",
        }
    if spec.get("funded"):
        return {"funded": True, "note": spec.get("cost_note", u._FUNDED_NOTE),
                "source": "x", "source_url": "x"}
    return {"funded": False, "note": spec.get("omit_tuition_reason", ""),
            "source": "x", "source_url": "x"}


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    outcomes = dict(u._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = u._program_standard(spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": u._SCHOOL_WEBSITE.get(spec["school"]),
        "department": spec["department"],
        "tracks": u._TRACKS_BY_SLUG.get(slug),
        "application_requirements": u._requirements_for(spec),
        "cost_data": _cost_for(spec),
        "outcomes_data": outcomes,
        "class_profile": None,
        "faculty_contacts": None,
        "external_reviews": u._REVIEWS_BY_SLUG.get(slug),
        "content_sources": u._program_content(spec["school"], spec["keywords"]),
        "cip_code": spec["cip"],
        "who_its_for": spec["who_its_for"],
    }


def test_catalog_breadth_and_shape():
    assert len(u.SCHOOLS) == 15
    assert len(u.PROGRAMS) >= 150
    assert len(set(u.PROGRAM_SLUGS)) == len(u.PROGRAM_SLUGS)
    assert len({(p["program_name"], p["degree_type"]) for p in u.PROGRAMS}) == len(u.PROGRAMS)
    assert sum(1 for p in u.PROGRAMS if p["degree_type"] == "professional") >= 3
    assert sum(1 for p in u.PROGRAMS if p["degree_type"] == "phd") >= 40
    assert u.RANKING_DATA["ownership_type"] == "public"
    assert "irvine" in u.DESCRIPTION.lower()
    # The seed ships 4 verified campus photos; apply() appends a verified 5th (gold gallery 4-5).
    assert len(u._EXTRA_CAMPUS_PHOTOS) >= 1
    assert "news.uci.edu" in u._INSTITUTION_CONTENT["news_rss"]


def test_every_program_has_core_matcher_fields():
    for p in u.PROGRAMS:
        assert (p.get("description") or "").strip(), f"{p['slug']} empty description"
        assert p.get("cip"), f"{p['slug']} missing cip_code"
        assert (p.get("who_its_for") or "").strip(), f"{p['slug']} missing who_its_for"
        assert p.get("department"), f"{p['slug']} missing department"
    # undergraduate non-resident scalar (public-budget signal) with both rates in the breakdown
    ug = u._undergrad_cost()
    assert ug["tuition_usd"] == u._UG_TUITION_NONRES
    assert ug["breakdown"]["tuition_in_state"] == u._UG_TUITION_RES
    assert ug["breakdown"]["tuition_out_of_state"] == u._UG_TUITION_NONRES


def test_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    bad = _gaps("institution", res, set(u._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant_or_omitted():
    for spec in u.SCHOOLS:
        snap = _school_snapshot(spec)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{spec['name']} gaps: {bad}"
        assert snap["content_sources"], f"{spec['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in u.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(u._program_standard(spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_programs_have_reviews():
    for slug in _COVERABLE_REVIEWS:
        assert slug in u._REVIEWS_BY_SLUG, slug
        assert u._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(u._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug
