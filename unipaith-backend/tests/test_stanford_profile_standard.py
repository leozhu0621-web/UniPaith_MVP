"""The Stanford profile conforms to the gold standard across its whole tree — the
institution, seven schools, and the full IPEDS/Scorecard program catalog — mirroring
the MIT/Sloan/MBAn and Berkeley reference certifications.

Pure (no DB): builds each node's persisted snapshot from ``stanford_profile`` and runs
``check_conformance``. The only gaps permitted are the fields each node honestly records
in its ``_standard.omitted`` lists. The Stanford GSB MBA is the deeply-enriched flagship.
"""

from unipaith.data import stanford_profile as s
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = "stanford-mba"
_OMITTABLE_SECTIONS = {"tracks", "insights"}


def _required_fields_of_section(level: str, section_id: str) -> set[str]:
    sec = next(sec for sec in MANIFEST[level] if sec.id == section_id)
    return {f.path for f in sec.fields if f.required and f.enrich}


def _gaps_are_all_omitted(level: str, res, omitted: set[str]) -> tuple[bool, set]:
    bad = set(res.missing_fields) - omitted
    for sec_id in res.missing_sections:
        if not _required_fields_of_section(level, sec_id) <= omitted:
            bad |= {f"section:{sec_id}"}
    return (not bad), bad


def _institution_snapshot() -> dict:
    school_outcomes = {**s.SCHOOL_OUTCOMES}
    for path in s._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            school_outcomes.pop(path.split(".", 1)[1], None)
    school_outcomes["_standard"] = s._standard(s._OMITTED_INSTITUTION)
    return {
        "description_text": s.DESCRIPTION,
        "student_body_size": s.UNDERGRAD_COUNT,
        "media_gallery": [s.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": s.RANKING_DATA,
        "school_outcomes": school_outcomes,
        "content_sources": s._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = s._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = s._standard(s._ABOUT_OMITTED.get(name, []))
    cs = s._GSB_CONTENT if name == s._GSB else s._school_content(name)
    return {
        "name": name,
        "description_text": next(sc["description"] for sc in s.SCHOOLS if sc["name"] == name),
        "website_url": s._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": cs,
    }


def _program_snapshot(slug: str) -> dict:
    spec = s._SPEC_BY_SLUG[slug]
    out_override = s._OUTCOMES_BY_SLUG.get(slug)
    fos = s._FOS_OUTCOMES.get(slug)
    if out_override is not None:
        outcomes = dict(out_override)
        has_program_outcomes = True
    elif fos is not None:
        salary, cip = fos
        outcomes = {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "earnings_timeframe": "median earnings 1 year after completion",
            "conditions": s._FOS_CONDITIONS,
            "source": "U.S. Dept. of Education College Scorecard — Field of Study",
            "source_url": "https://collegescorecard.ed.gov/school/?243744",
        }
        has_program_outcomes = True
    else:
        outcomes = dict(s._OUTCOMES_INSTITUTION)
        has_program_outcomes = False
    outcomes["_standard"] = s._program_standard(slug, spec, has_program_outcomes)
    cost_override = s._COST_BY_SLUG.get(slug)
    if cost_override is not None:
        cost = dict(cost_override)
    elif spec["degree_type"] == "phd":
        cost = {
            "tuition_usd": 0,
            "funded": True,
            "source": "Stanford Graduate Admissions",
            "source_url": "https://gradadmissions.stanford.edu/",
        }
    elif spec["degree_type"] == "bachelors":
        cost = {
            "tuition_usd": s._TUITION_UNDERGRAD,
            "source": "Stanford Student Services",
            "source_url": "https://studentservices.stanford.edu/tuition-rates/2025-2026-undergraduate-tuition-rates",
        }
    else:
        cost = {
            "funded": spec["degree_type"] == "phd",
            "note": "see program website",
            "source": "Stanford Graduate Admissions",
            "source_url": "https://gradadmissions.stanford.edu/",
        }
    if slug == s._FLAGSHIP:
        req = s._REQ_MBA
    elif spec["degree_type"] == "professional":
        req = s._REQ_PROFESSIONAL
    elif spec["degree_type"] == "bachelors":
        req = s._REQ_UNDERGRAD
    else:
        req = s._REQ_GRAD
    return {
        "program_name": s._FULL_NAME_BY_SLUG.get(slug) or spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": s._WEBSITE_BY_SLUG.get(slug) or s._SCHOOL_WEBSITE.get(spec["school"]),
        "highlights": s._HL_BY_SLUG.get(slug) or s._HL_BASELINE,
        "who_its_for": s._WHO_BY_SLUG.get(slug) or s._WHO_BASELINE,
        "tracks": s._TRACKS_BY_SLUG.get(slug),
        "application_requirements": req,
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": s._CLASS_PROFILE_BY_SLUG.get(slug, {}),
        "faculty_contacts": s._FACULTY_BY_SLUG.get(slug, {}),
        "external_reviews": s._REVIEWS_BY_SLUG.get(slug, {}),
        "content_sources": s._MBA_CONTENT if slug == _FLAGSHIP else s._program_content(spec),
    }


def test_stanford_institution_is_gold_except_recorded_omission():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    omitted = set(s._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, (
        f"Unexpected institution gaps: {res.missing_fields} {res.missing_sections}"
    )
    ok, bad = _gaps_are_all_omitted("institution", res, omitted)
    assert ok, f"Unexpected institution section gaps: {bad}"
    assert s.SCHOOL_OUTCOMES.get("media_credit")
    photos = s.SCHOOL_OUTCOMES.get("campus_photos") or []
    assert len(photos) >= 4
    for photo in photos:
        assert photo.get("url") and photo.get("credit")
    assert "private research university" in s.DESCRIPTION.lower()


def test_every_school_is_gold_except_recorded_omissions():
    assert len(s.SCHOOLS) == 7
    for school in s.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        allowed = set(s._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= allowed, (
            f"{name} unexpected gaps: {res.missing_fields} {res.missing_sections}"
        )
        ok, bad = _gaps_are_all_omitted("school", res, allowed)
        assert ok, f"{name} unexpected section gaps: {bad}"


def test_mba_flagship_is_deeply_enriched():
    assert _FLAGSHIP in s._TRACKS_BY_SLUG
    assert _FLAGSHIP in s._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in s._FACULTY_BY_SLUG
    assert _FLAGSHIP in s._REVIEWS_BY_SLUG
    assert s._program_standard(_FLAGSHIP, s._SPEC_BY_SLUG[_FLAGSHIP], True)["omitted"] == []


def test_coverable_programs_have_external_reviews():
    """Hand-gathered external_reviews ship only on verified flagship slugs (miss #8)."""
    coverable = [
        _FLAGSHIP,
        "stanford-cs-ms",
        "stanford-cs-bs",
        "stanford-economics-bs",
        "stanford-ee-ms",
        "stanford-me-bs",
        "stanford-mse-ms",
        "stanford-bioe-bs",
        "stanford-human-biology-bs",
        "stanford-symbolic-systems-bs",
        "stanford-msx",
        "stanford-jd",
        "stanford-md",
    ]
    assert len(coverable) == len(s._REVIEWS_BY_SLUG)
    for slug in coverable:
        assert slug in s._REVIEWS_BY_SLUG, slug
        assert s._REVIEWS_BY_SLUG[slug].get("summary"), slug
        assert len(s._REVIEWS_BY_SLUG[slug].get("sources", [])) >= 2, slug


def test_every_program_is_gold_except_recorded_omissions():
    assert len(s.PROGRAMS) >= 170, "full IPEDS/Scorecard catalog breadth (UNITID 243744)"
    for spec in s.PROGRAMS:
        slug = spec["slug"]
        res = check_conformance(
            "program", _program_snapshot(slug), profile_version=STANDARD_VERSION
        )
        fos = s._FOS_OUTCOMES.get(slug)
        has_fos = fos is not None or slug in s._OUTCOMES_BY_SLUG
        allowed = set(
            s._program_standard(slug, spec, has_program_outcomes=has_fos)["omitted"]
        )
        assert set(res.missing_fields) <= allowed, (
            f"{slug} unexpected field gaps: {res.missing_fields}"
        )
        assert set(res.missing_sections) <= _OMITTABLE_SECTIONS, (
            f"{slug} unexpected section gaps: {res.missing_sections}"
        )


def test_catalog_quality_gate():
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(s.PROGRAMS)
    assert not errors, f"Catalog quality gate failed: {errors}"


def test_catalog_breadth_and_shape():
    assert len(s.PROGRAMS) >= 170, "full Scorecard catalog breadth (UNITID 243744)"
    assert len(set(s.PROGRAM_SLUGS)) == len(s.PROGRAM_SLUGS)
    assert s.RANKING_DATA["ownership_type"] == "private_nonprofit"
    assert (
        "private" in s.DESCRIPTION.lower()
        and "research university" in s.DESCRIPTION.lower()
    )


def test_no_name_prefixed_descriptions():
    name_prefix = sum(
        1
        for prog in s.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, (
        f"{name_prefix} programs still prefix description with program_name"
    )


def test_no_identical_across_credential_levels():
    from collections import Counter

    desc_counts = Counter(prog.get("description") for prog in s.PROGRAMS)
    shared = sum(c for c in desc_counts.values() if c >= 2)
    assert shared == 0, (
        f"{shared} programs share a description verbatim with a credential sibling"
    )


def test_stanford_catalog_has_no_frame_stripped_shared_body():
    from unipaith.profile_standard.anti_stub import analyze, frame_stripped_shared_body

    report = analyze(s.PROGRAMS)
    assert report.is_clean
    shared = frame_stripped_shared_body(s.PROGRAMS, abs_chars=150)
    assert not shared, (
        f"Stanford credential siblings share a 150+-char body on "
        f"{len(shared)} field(s): {shared[:8]}{' …' if len(shared) > 8 else ''}"
    )


def test_no_peer_contaminated_descriptions():
    peer_signatures = (
        "Kelly Writers House",
        "Morris Arboretum",
        "GRASP",
        "Warren Center",
        "Longwood",
        " GSAS ",
        "Sibley School",
        "Perry World House",
        "Krieger",
        "Fels Institute",
        "Carpenter Center",
        "Burke Library",
        "Mahoney Institute",
        "Singh Center",
        "Atkinson Center",
        "Faculty of Arts & Sciences",
        "Johns Stanford",
        "Weill Stanford",
        "Graduate School of Journalism",
        "Institute of Contemporary Art",
        "Language Data Institute",
        "College of Veterinary Medicine",
        "Visual and Environmental Studies",
        "School of Public Health",
        "Laboratory for Research on the Structure of Matter",
    )
    contaminated = sum(
        1
        for prog in s.PROGRAMS
        if any(sig in (prog.get("description") or "") for sig in peer_signatures)
    )
    assert contaminated == 0, (
        f"{contaminated} programs still carry peer-institution signatures"
    )


def test_every_node_has_content_sources():
    assert s._INSTITUTION_CONTENT.get("news_rss")
    assert s._INSTITUTION_CONTENT.get("events_feed")
    for school in s.SCHOOLS:
        cs = s._GSB_CONTENT if school["name"] == s._GSB else s._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), school["name"]
    for spec in s.PROGRAMS:
        cs = s._MBA_CONTENT if spec["slug"] == _FLAGSHIP else s._program_content(spec)
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), spec["slug"]
