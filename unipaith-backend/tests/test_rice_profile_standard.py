"""The Rice profile conforms to the gold standard for its institution, every one of its
eight schools, and its full breadth-first program catalog.

Pure (no DB): builds each node's persisted snapshot from the ``rice_profile`` module and
runs ``check_conformance``. A node is accepted only when it is gold OR every remaining
required field is recorded in that node's ``_standard.omitted`` (verified-unavailable) with
a real reason.
"""

# ruff: noqa: E501

from unipaith.data import rice_profile as r
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_FLAGSHIP = r._FLAGSHIP


def _institution_snapshot() -> dict:
    so = {**r.SCHOOL_OUTCOMES}
    for path in r._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            so.pop(path.split(".", 1)[1], None)
    so["_standard"] = r._standard(r._OMITTED_INSTITUTION)
    return {
        "description_text": r.DESCRIPTION,
        "student_body_size": r.UNDERGRAD_COUNT,
        "media_gallery": [r.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": r.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": r._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = r._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = r._standard(r._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in r.SCHOOLS if s["name"] == name),
        "website_url": r._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": r._school_content(name),
    }


def _program_cost(spec: dict):
    if spec["degree_type"] == "bachelors":
        return {
            "tuition_usd": r._TUITION_UG,
            "source": r._COST_SRC[0],
            "source_url": r._COST_SRC[1],
        }
    published = r._published_grad_cost(spec)
    if published is not None:
        return published
    return {
        "note": "funded or see Rice Bursar graduate tuition pages",
        "source": "Rice University Bursar",
        "source_url": "https://bursar.rice.edu/tuition_fee_rates/graduate-programs",
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    if slug == _FLAGSHIP:
        outcomes = dict(r._MBA_OUTCOMES)
    else:
        outcomes = dict(r._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = r._program_standard(slug, spec)
    _kw = r._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
        r._SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
    )
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": spec.get("website") or r._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": r._TRACKS_BY_SLUG.get(slug),
        "application_requirements": r._requirements_for(spec),
        "cost_data": _program_cost(spec),
        "outcomes_data": outcomes,
        "class_profile": r._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": r._FACULTY_BY_SLUG.get(slug),
        "external_reviews": r._REVIEWS_BY_SLUG.get(slug),
        "content_sources": r._program_content(spec["school"], _kw),
    }


def _section_gaps_unexpected(level: str, missing_sections: list[str], omitted: set[str]) -> list:
    """A missing required section is acceptable only when ALL its required enrich-fields are
    recorded in this node's omitted list."""
    bad = []
    for secid in missing_sections:
        sec = next(s for s in MANIFEST[level] if s.id == secid)
        req = {f.path for f in sec.fields if f.enrich and f.required}
        if not req <= omitted:
            bad.append(secid)
    return bad


def test_institution_is_gold():
    res = check_conformance("institution", _institution_snapshot(), profile_version=STANDARD_VERSION)
    omitted = set(r._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, f"Unexpected institution gaps: {res.missing_fields}"
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)
    assert r.SCHOOL_OUTCOMES.get("media_credit")
    photos = r.SCHOOL_OUTCOMES.get("campus_photos") or []
    assert len(photos) >= 4
    for photo in photos:
        assert photo.get("url") and photo.get("credit")


def test_all_eight_schools_done():
    assert len(r.SCHOOLS) == 8
    assert {s["name"] for s in r.SCHOOLS} == set(r._SCHOOL_WEBSITE)
    for school in r.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(r._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, f"{name}: unexpected gaps {res.missing_fields}"
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name


def test_rice_mba_flagship_is_deeply_enriched():
    assert _FLAGSHIP in r._TRACKS_BY_SLUG
    assert _FLAGSHIP in r._CLASS_PROFILE_BY_SLUG
    assert _FLAGSHIP in r._REVIEWS_BY_SLUG
    assert r._program_standard(_FLAGSHIP, r._SPEC_BY_SLUG[_FLAGSHIP])["omitted"] == []


def test_coverable_programs_have_external_reviews():
    coverable = [
        _FLAGSHIP,
        "rice-computer-science-ug",
        "rice-master-of-computer-science-mcs-rice-online-prof",
        "rice-master-of-data-science-mds-rice-online-prof",
        "rice-master-of-architecture-march-option-1-professional-prof",
        "rice-economics-ug",
    ]
    for slug in coverable:
        assert slug in r._REVIEWS_BY_SLUG, slug
        assert r._REVIEWS_BY_SLUG[slug].get("summary"), slug


def test_graduate_tiers_carry_published_tuition():
    """REPAIR_BACKLOG #4 — master's/professional tiers must not be matcher-blind on budget."""
    for spec in r.PROGRAMS:
        dtype = spec["degree_type"]
        if dtype in ("masters", "professional", "certificate"):
            assert r._grad_has_verified_tuition(spec), spec["slug"]
        elif dtype == "phd":
            assert not r._grad_has_verified_tuition(spec), spec["slug"]


def test_every_program_is_done():
    assert len(r.PROGRAMS) >= 150, "breadth-first catalog should be the full program set"
    for spec in r.PROGRAMS:
        res = check_conformance("program", _program_snapshot(spec), profile_version=STANDARD_VERSION)
        omitted = set(r._program_standard(spec["slug"], spec)["omitted"])
        assert set(res.missing_fields) <= omitted, f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), spec["slug"]


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in r.SCHOOLS}
    for spec in r.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(r.PROGRAM_SLUGS) == len(set(r.PROGRAM_SLUGS)), "duplicate program slug"


def test_every_program_has_delivery_format():
    assert {p["delivery_format"] for p in r.PROGRAMS} <= {"in_person", "online", "hybrid"}
    assert any(p["delivery_format"] == "online" for p in r.PROGRAMS)
    assert any(p["delivery_format"] == "hybrid" for p in r.PROGRAMS)


def test_every_node_has_content_sources():
    assert r._INSTITUTION_CONTENT.get("news_rss")
    for school in r.SCHOOLS:
        cs = r._school_content(school["name"])
        assert cs.get("news_rss") and cs.get("events_feed"), school["name"]


def test_no_name_prefixed_descriptions():
    name_prefix = sum(
        1
        for prog in r.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, f"{name_prefix} programs still prefix description with program_name"


def test_catalog_is_structurally_real():
    """Per-row realness + anti-stub gate (REPAIR BACKLOG #4 — gold MIT = 0%)."""
    import re

    from unipaith.profile_standard.anti_stub import analyze

    report = analyze(r.PROGRAMS)
    assert report.is_clean, f"anti-stub not clean: {report.summary()}"
    for spec in r.PROGRAMS:
        name = spec["program_name"]
        assert not re.match(r"^(Bachelor's|Master's|Doctorate) in ", name), (
            f"possessive-mint name: {name}"
        )
        assert spec.get("department"), f"{spec['slug']} missing department"
        assert spec["department"] != name, f"dept-echo name: {spec['slug']}"


def test_no_identical_across_credential_levels():
    from collections import Counter

    desc_counts = Counter(prog.get("description") for prog in r.PROGRAMS)
    shared = sum(c for c in desc_counts.values() if c >= 2)
    assert shared == 0, (
        f"{shared} programs share a description verbatim with a credential sibling"
    )


def test_matcher_core_cip_code_complete():
    """Every program carries a real NCES CIP-2020 6-digit code (REPAIR_BACKLOG #1)."""
    import json
    import pathlib
    import re

    ref_path = pathlib.Path(r.__file__).parents[3] / "data" / "reference" / "ref_majors.jsonl"
    ref = {json.loads(line)["cip_code"] for line in open(ref_path)}
    missing = [s for s in r.PROGRAM_SLUGS if not r.CIP6_BY_SLUG.get(s)]
    assert not missing, f"cip_code missing on {len(missing)} rows: {missing[:5]}"
    bad_form = [s for s, c in r.CIP6_BY_SLUG.items() if not re.fullmatch(r"\d{2}\.\d{4}", c)]
    assert not bad_form, f"malformed CIP codes: {bad_form[:5]}"
    not_ref = [(s, c) for s, c in r.CIP6_BY_SLUG.items() if c not in ref]
    assert not not_ref, f"CIP codes absent from ref_majors (not real): {not_ref[:5]}"


def test_matcher_core_who_its_for_distinct():
    """who_its_for filled on every program AND program-DISTINCT, never a degree-type
    template (REPAIR_BACKLOG #4; gold field-specific catalogs are ~1.0)."""
    missing = [s for s in r.PROGRAM_SLUGS if not (r.WHO_BY_SLUG.get(s) or "").strip()]
    assert not missing, f"who_its_for missing/blank on {len(missing)} rows: {missing[:5]}"
    vals = [r.WHO_BY_SLUG[s] for s in r.PROGRAM_SLUGS]
    ratio = len(set(vals)) / len(vals)
    assert ratio >= 0.9, f"who_its_for type-gamed: distinct/total {ratio:.2f} < 0.9"
