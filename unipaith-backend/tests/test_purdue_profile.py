"""The Purdue profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 10 real schools, and every one of its programs —
mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``purdue_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import purdue_profile as p
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
    m = next(x for x in p._SCHOOL_META if x["name"] == name)
    about = {**p._about_for(m), "_standard": p._standard(p._about_omitted(m))}
    return {
        "name": name,
        "description_text": p._school_description(m),
        "website_url": m["website"],
        "about_detail": about,
        "content_sources": p._school_content(name),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    cost = (
        {
            "tuition_usd": p._TUITION_UG_INSTATE,
            "total_cost_of_attendance": p._UNDERGRAD_COA,
            "avg_net_price": p._AVG_NET_PRICE,
            "breakdown": {
                "tuition_in_state": p._TUITION_UG_INSTATE,
                "tuition_out_of_state": p._TUITION_UG_OOS,
            },
            "funded": False,
            "source": p._COST_SRC[0],
            "source_url": p._COST_SRC[1],
        }
        if spec["degree_type"] == "bachelors"
        else (
            {
                "tuition_usd": 0,
                "funded": True,
                "source": "Purdue Graduate School — Funding",
                "source_url": "https://www.purdue.edu/gradschool/prospective/financing/",
            }
            if spec["degree_type"] == "phd"
            else {
                "note": "see program page",
                "source": "Purdue program tuition page",
                "source_url": p._website_for(spec),
            }
        )
    )
    outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug, spec)
    kw = p._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(p._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": p._website_for(spec),
        "department": spec.get("department"),
        "tracks": p._TRACKS_BY_SLUG.get(slug),
        "application_requirements": p._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": p._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": p._FACULTY_BY_SLUG.get(slug),
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug),
        "content_sources": p._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(p.SCHOOLS) == 10
    assert len(p.PROGRAMS) >= 300
    assert len(set(p.PROGRAM_SLUGS)) == len(p.PROGRAM_SLUGS)
    assert p.RANKING_DATA["ownership_type"] == "public"
    assert "public land-grant research university in west lafayette" in p.DESCRIPTION.lower()
    assert len(p.SCHOOL_OUTCOMES["campus_photos"]) >= 4


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(p._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for m in p._SCHOOL_META:
        snap = _school_snapshot(m["name"])
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{m['name']} gaps: {bad}"
        assert snap["content_sources"], f"{m['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in p.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(p._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_programs_have_reviews():
    reviewed = [s for s in p._REVIEWS_BY_SLUG if s in p.PROGRAM_SLUGS]
    assert len(reviewed) >= 10
