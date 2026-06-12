"""The Duke profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its ten schools, and every program — mirroring the
MIT/Sloan/MBAn and Cornell reference certifications.

Pure (no DB): builds each node's persisted snapshot from the duke_profile module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes when it
is gold OR every remaining required gap is recorded in that node's ``_standard.omitted``.
"""

from unipaith.data import duke_profile as d
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST


def _required_fields_of_section(level: str, section_id: str) -> set[str]:
    sec = next(s for s in MANIFEST[level] if s.id == section_id)
    return {f.path for f in sec.fields if f.required and f.enrich}


def _gaps_are_all_omitted(level: str, res, omitted: set[str]) -> tuple[bool, set]:
    bad = set(res.missing_fields) - omitted
    for sec_id in res.missing_sections:
        if not _required_fields_of_section(level, sec_id) <= omitted:
            bad |= {f"section:{sec_id}"}
    return (not bad), bad


def _program_cost(spec: dict):
    if spec["degree_type"] == "bachelors":
        return {
            "tuition_usd": d._TUITION_UG,
            "source": d._COST_SRC[0],
            "source_url": d._COST_SRC[1],
        }
    grad = d._grad_cost(spec)
    if grad is not None:
        return grad
    return {"note": "see school page", "source": "x", "source_url": "x"}


def _program_snapshot(slug: str) -> dict:
    spec = next(p for p in d.PROGRAMS if p["slug"] == slug)
    if slug == d._FLAGSHIP:
        outcomes = dict(d._MBA_OUTCOMES)
    else:
        outcomes = dict(d._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = d._program_standard(slug, spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": spec.get("website") or d._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": d._TRACKS_BY_SLUG.get(slug),
        "application_requirements": d._requirements_for(spec),
        "cost_data": _program_cost(spec),
        "outcomes_data": outcomes,
        "class_profile": d._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": d._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": d._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": d._program_content(
            spec["school"],
            d._PROGRAM_KEYWORDS_BY_SLUG.get(slug, ["x"]),
        ),
    }


def _school_snapshot(name: str) -> dict:
    about = d._ABOUT_DETAIL.get(name)
    return {
        "name": name,
        "description_text": next(s["description"] for s in d.SCHOOLS if s["name"] == name),
        "website_url": d._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": d._school_content(name),
    }


def _institution_snapshot() -> dict:
    return {
        "description_text": d.DESCRIPTION,
        "student_body_size": d.UNDERGRAD_COUNT,
        "media_gallery": [d._CAMPUS_PHOTO],
        "ranking_data": d.RANKING_DATA,
        "school_outcomes": d.SCHOOL_OUTCOMES,
        "content_sources": d._INSTITUTION_CONTENT,
    }


def test_duke_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert set(res.missing_fields) <= set(d._OMITTED_INSTITUTION), (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    assert not res.missing_sections


def test_every_school_is_conformant():
    for school in d.SCHOOLS:
        snap = _school_snapshot(school["name"])
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        allowed = set(d._ABOUT_OMITTED.get(school["name"], []))
        assert set(res.missing_fields) <= allowed, (
            f"{school['name']} gaps: {res.missing_fields} {res.missing_sections}"
        )
        assert not res.missing_sections, (
            f"{school['name']} missing sections: {res.missing_sections}"
        )


def test_every_program_is_conformant_or_omitted():
    for spec in d.PROGRAMS:
        slug = spec["slug"]
        snap = _program_snapshot(slug)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(d._program_standard(slug, spec)["omitted"])
        ok, bad = _gaps_are_all_omitted("program", res, omitted)
        assert ok, f"{slug} has un-omitted gaps: {bad}"


def test_structure_integrity():
    school_names = {s["name"] for s in d.SCHOOLS}
    for spec in d.PROGRAMS:
        assert spec["school"] in school_names, f"{spec['slug']} maps to unknown school"
    assert len(d.PROGRAM_SLUGS) == len(set(d.PROGRAM_SLUGS)), "duplicate program slug"
    assert len(d.PROGRAMS) >= 150, "Duke catalog should cover the full program set"


def test_every_node_has_content_sources():
    assert d._INSTITUTION_CONTENT.get("news_rss")
    for school in d.SCHOOLS:
        cs = d._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed"), school["name"]
    for spec in d.PROGRAMS:
        cs = d._program_content(
            spec["school"],
            d._PROGRAM_KEYWORDS_BY_SLUG.get(spec["slug"], ["x"]),
        )
        assert cs.get("news_rss") and cs.get("keywords"), spec["slug"]


def test_every_node_has_standard_stamp():
    assert d._standard(d._OMITTED_INSTITUTION)["version"] == STANDARD_VERSION
    for spec in d.PROGRAMS:
        st = d._program_standard(spec["slug"], spec)
        assert st["version"] == STANDARD_VERSION and st["enriched_at"] == d.ENRICHED_AT


def test_institution_has_media_credit():
    assert d.SCHOOL_OUTCOMES.get("media_credit"), "Campus photo must carry attribution"


def test_coverable_programs_have_reviews():
    expected = {
        d._FLAGSHIP,
        "duke-computer-science-ab",
        "duke-juris-doctor-jd-prof",
        "duke-doctor-of-medicine-md-prof",
        "duke-master-of-public-policy-mpp-ms",
        "duke-economics-ab",
        "duke-electrical-and-computer-engineering-bse",
        "duke-public-policy-studies-ab",
    }
    reviewed = {
        slug for slug, rev in d._REVIEWS_BY_SLUG.items() if rev and rev.get("summary")
    }
    assert expected <= reviewed, f"Missing reviews for {expected - reviewed}"


def test_fuqua_mba_flagship_is_deeply_enriched():
    slug = d._FLAGSHIP
    spec = next(p for p in d.PROGRAMS if p["slug"] == slug)
    snap = _program_snapshot(slug)
    res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
    omitted = set(d._program_standard(slug, spec)["omitted"])
    assert res.conformant or set(res.missing_fields) <= omitted, (
        f"MBA gaps: {set(res.missing_fields) - omitted}"
    )
    assert d._MBA_OUTCOMES["median_salary"] == 160000
    assert snap["external_reviews"].get("summary")
    assert snap["tracks"] is not None
    assert snap["class_profile"].get("cohort_size")
