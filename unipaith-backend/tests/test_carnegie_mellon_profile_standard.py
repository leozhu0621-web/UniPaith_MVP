"""The Carnegie Mellon profile conforms to the gold standard for its institution,
every one of its seven schools, and its full breadth-first program catalog.

Pure (no DB): builds each node's persisted snapshot from the
``carnegie_mellon_profile`` module and runs ``check_conformance``. A node is
accepted only when it is gold OR every remaining required field is recorded in
that node's ``_standard.omitted`` (verified-unavailable) with a real reason.
"""

# ruff: noqa: E501

from unipaith.data import carnegie_mellon_profile as c
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "cmu-mba"


def _is_coverable(spec: dict) -> bool:
    keywords = (
        "mba", "mban", "computer science", "data science", "analytics", "finance",
        "engineering", "public health", "mph", "mpp", "jd", "law", "medicine", "md",
        "architecture", "economics", "business", "nursing", "mscs", "mfin", "meng",
        "social work", "journalism", "hospitality", "film", "biomedical", "march",
        "mha", "mfa", "msw", "dmd", "dentistry",
    )
    pname = (spec.get("program_name") or "").lower()
    slug = (spec.get("slug") or "").lower()
    dtype = spec.get("degree_type", "")
    if dtype not in ("bachelors", "masters", "professional", "doctoral", "phd"):
        return False
    return any(k in pname or k in slug for k in keywords)


def _institution_snapshot() -> dict:
    so = {**c.SCHOOL_OUTCOMES}
    for path in c._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            so.pop(path.split(".", 1)[1], None)
    so["_standard"] = c._standard(c._OMITTED_INSTITUTION)
    return {
        "description_text": c.DESCRIPTION,
        "student_body_size": c.UNDERGRAD_COUNT,
        "media_gallery": [c.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": c.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": c._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = c._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = c._standard(c._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in c.SCHOOLS if s["name"] == name),
        "website_url": c._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": c._school_content(name),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    if slug == _FLAGSHIP:
        outcomes = dict(c._MBA_OUTCOMES)
    elif spec["degree_type"] in ("bachelors", "masters", "phd"):
        outcomes = dict(c._OUTCOMES_INSTITUTION)
    else:
        outcomes = {}
    outcomes["_standard"] = c._program_standard(slug, spec)
    cost_override = c._COST_BY_SLUG.get(slug)
    tuition, cost = c._program_tuition(spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": c._description_for(spec),
        "website_url": spec["website_url"],
        "department": spec["department"],
        "tracks": c._TRACKS_BY_SLUG.get(slug),
        "application_requirements": c._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": c._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": c._FACULTY_BY_SLUG.get(slug),
        "external_reviews": c._REVIEWS_BY_SLUG.get(slug),
        "content_sources": (
            c._MBA_CONTENT if slug == _FLAGSHIP else c._program_content_for(spec)
        ),
    }


def _omitted_for(spec: dict) -> set[str]:
    return set(c._program_standard(spec["slug"], spec)["omitted"])


def _section_gaps_unexpected(level: str, missing_sections: list[str], omitted: set[str]) -> list:
    """A missing required section is acceptable only when ALL its required
    enrich-fields are recorded in this node's omitted list."""
    bad = []
    for secid in missing_sections:
        sec = next(s for s in MANIFEST[level] if s.id == secid)
        req = {f.path for f in sec.fields if f.enrich and f.required}
        if not req <= omitted:
            bad.append(secid)
    return bad


def test_institution_is_gold_except_recorded_omissions():
    res = check_conformance("institution", _institution_snapshot(), profile_version=STANDARD_VERSION)
    omitted = set(c._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, f"Unexpected institution gaps: {res.missing_fields}"
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)
    assert c.SCHOOL_OUTCOMES.get("media_credit")
    assert "school_outcomes.employed_or_continuing_ed" in omitted
    assert "school_outcomes.top_employer_industries" in omitted


def test_institution_has_campus_photo_gallery():
    photos = c.SCHOOL_OUTCOMES.get("campus_photos") or []
    assert len(photos) >= 4, "CMU needs a 4–5 photo verified campus gallery"
    for photo in photos:
        assert photo.get("url") and photo.get("credit"), photo
    assert c._CAMPUS_PHOTO == photos[0]["url"]


def test_all_seven_schools_done():
    assert len(c.SCHOOLS) == 7
    assert {s["name"] for s in c.SCHOOLS} == set(c._SCHOOL_WEBSITE)
    for school in c.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(c._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, f"{name}: unexpected gaps {res.missing_fields}"
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name
        cs = c._school_content(name)
        assert cs["news_rss"] and cs["events_feed"] and cs["keywords"], name


def test_tepper_mba_flagship_is_deeply_enriched():
    assert _FLAGSHIP in c._TRACKS_BY_SLUG
    assert _FLAGSHIP in c._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in c._REVIEWS_BY_SLUG
    assert _FLAGSHIP in c._COST_BY_SLUG
    assert c._program_standard(_FLAGSHIP)["omitted"] == [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "faculty_contacts.lead",
    ]


def test_coverable_programs_carry_external_reviews():
    coverable = [p for p in c.PROGRAMS if _is_coverable(p)]
    assert len(coverable) >= 70
    for spec in coverable:
        slug = spec["slug"]
        assert slug in c._REVIEWS_BY_SLUG, slug
        assert c._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(c._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_every_program_is_done():
    assert len(c.PROGRAMS) >= 150, "breadth-first catalog should be the full program set"
    for spec in c.PROGRAMS:
        res = check_conformance("program", _program_snapshot(spec), profile_version=STANDARD_VERSION)
        omitted = _omitted_for(spec)
        assert set(res.missing_fields) <= omitted, (
            f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        )
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), spec["slug"]
        assert "content_sources" not in omitted, spec["slug"]
        cs = (
            c._MBA_CONTENT
            if spec["slug"] == _FLAGSHIP
            else c._program_content_for(spec)
        )
        assert cs["news_rss"] and cs["events_feed"] and cs["keywords"], spec["slug"]


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in c.SCHOOLS}
    for spec in c.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(c.PROGRAM_SLUGS) == len(set(c.PROGRAM_SLUGS)), "duplicate program slug"


def test_every_program_has_delivery_format():
    assert {p["delivery_format"] for p in c.PROGRAMS} <= {"in_person", "online", "hybrid"}
    for spec in c.PROGRAMS:
        assert spec["delivery_format"], f"{spec['slug']} missing delivery_format"
    assert any(p["delivery_format"] == "online" for p in c.PROGRAMS)
    assert any(p["delivery_format"] == "hybrid" for p in c.PROGRAMS)


def test_matcher_core_tuition_is_published_catalog_wide():
    """Graduate-tier NULL is matcher starvation — every row carries a cited rate or
    an honest per-program omission (REPAIR_BACKLOG run 75 HIGH #3)."""
    missing = []
    for spec in c.PROGRAMS:
        tuition, cost = c._program_tuition(spec)
        if tuition is None:
            omitted = c._program_standard(spec["slug"], spec)["omitted"]
            assert "cost_data.tuition_usd" in omitted, spec["slug"]
            assert cost and cost.get("note"), spec["slug"]
            missing.append(spec["slug"])
    assert len(missing) == 1 and missing == ["cmu-cert-fds-online"], (
        f"unexpected tuition gaps: {missing}"
    )
    covered = sum(1 for spec in c.PROGRAMS if c._program_tuition(spec)[0] is not None)
    assert covered == len(c.PROGRAMS) - 1


def test_graduate_tiers_carry_published_tuition():
    """Whole graduate tiers at 0% is a hard fail — master's and Ph.D. must be filled."""
    from collections import Counter

    by_dt: Counter[str] = Counter()
    null_by_dt: Counter[str] = Counter()
    for spec in c.PROGRAMS:
        dt = spec["degree_type"]
        by_dt[dt] += 1
        if c._program_tuition(spec)[0] is None:
            null_by_dt[dt] += 1
    assert null_by_dt["masters"] == 0, (
        f"master's tier missing tuition on {null_by_dt['masters']}/{by_dt['masters']}"
    )
    assert null_by_dt["phd"] == 0, (
        f"PhD tier should carry tuition 0 (funded) or a sticker, not null — "
        f"{null_by_dt['phd']}/{by_dt['phd']} null"
    )


def test_graduate_tuition_not_undergrad_copy_down():
    """Graduate rows must not carry the undergraduate sticker (value-correctness)."""
    ug = c._TUITION_UNDERGRAD
    copydown = [
        p["slug"]
        for p in c.PROGRAMS
        if p["degree_type"] != "bachelors" and c._program_tuition(p)[0] == ug
    ]
    assert not copydown, f"undergrad sticker on graduate rows: {copydown[:8]}"
