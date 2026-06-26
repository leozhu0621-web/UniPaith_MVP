"""The JHU profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 10 real schools, and every one of its programs —
mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``jhu_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import jhu_profile as j
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
    so = {**j.SCHOOL_OUTCOMES, "_standard": j._standard(j._OMITTED_INSTITUTION)}
    return {
        "description_text": j.DESCRIPTION,
        "student_body_size": j.UNDERGRAD_COUNT,
        "media_gallery": [j.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": j.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": j._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    m = next(x for x in j._SCHOOL_META if x["name"] == name)
    about = {**j._about_for(m), "_standard": j._standard(j._about_omitted(m))}
    return {
        "name": name,
        "description_text": j._school_description(m),
        "website_url": m["website"],
        "about_detail": about,
        "content_sources": j._school_content(name),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    _tuition, cost = j._program_tuition(spec)
    outcomes = dict(j._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = j._program_standard(slug, spec)
    kw = j._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(j._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": j._website_for(spec),
        "department": spec.get("department"),
        "tracks": j._TRACKS_BY_SLUG.get(slug),
        "application_requirements": j._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": j._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": j._FACULTY_BY_SLUG.get(slug),
        "external_reviews": j._REVIEWS_BY_SLUG.get(slug),
        "content_sources": j._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(j.SCHOOLS) == 10
    assert len(j.PROGRAMS) >= 200
    assert len(set(j.PROGRAM_SLUGS)) == len(j.PROGRAM_SLUGS)
    assert sum(1 for p in j.PROGRAMS if p["delivery_format"] == "online") >= 10
    assert j.RANKING_DATA["ownership_type"] == "private"
    assert "private research university in baltimore" in j.DESCRIPTION.lower()
    assert len(j.SCHOOL_OUTCOMES["campus_photos"]) >= 4


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(j._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for m in j._SCHOOL_META:
        snap = _school_snapshot(m["name"])
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{m['name']} gaps: {bad}"
        assert snap["content_sources"], f"{m['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in j.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(j._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_programs_have_reviews():
    reviewed = [s for s in j._REVIEWS_BY_SLUG if s in j.PROGRAM_SLUGS]
    assert len(reviewed) >= 10


def test_catalog_has_no_padding_stubs():
    """Catalog must not carry CIP×award-level padding stubs."""
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(j.PROGRAMS)
    assert not errors, f"Catalog padding detected: {errors}"
    assert all(spec.get("department") for spec in j.PROGRAMS), "every program needs a department"
    names = [spec["program_name"] for spec in j.PROGRAMS]
    assert len(names) == len(set(names)), "duplicate program_name values"
    classif = sum(
        1
        for prog in j.PROGRAMS
        if j._CLASSIFICATION_STUB_RE.match(prog.get("description") or "")
    )
    assert classif == 0, f"{classif} programs still carry classification-only descriptions"
    name_prefix = sum(
        1
        for prog in j.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, f"{name_prefix} programs still prefix description with program_name"


def test_catalog_is_anti_stub_clean():
    """Per-credential bodies — gold MIT = 0% frame-stripped shared body (REPAIR HIGH #5)."""
    from unipaith.profile_standard.anti_stub import analyze, frame_stripped_shared_body

    report = analyze(j.PROGRAMS)
    assert report.is_clean, f"anti-stub not clean: {report.summary()}"
    shared = frame_stripped_shared_body(j.PROGRAMS)
    assert not shared, (
        f"credential siblings share a frame-stripped body on "
        f"{len(shared)} field(s): {shared[:8]}"
    )


def test_matcher_core_tuition_is_published_catalog_wide():
    """Tuition is institution-published — every program carries a cited rate (REPAIR #2)."""
    missing = [spec["slug"] for spec in j.PROGRAMS if j._program_tuition(spec)[0] is None]
    assert not missing, f"programs missing published tuition: {missing[:8]}"
    covered = sum(1 for spec in j.PROGRAMS if j._program_tuition(spec)[0] is not None)
    assert covered == len(j.PROGRAMS)


def test_matcher_core_cip_code_complete_and_well_formed():
    """Every program carries a 6-digit NCES cip_code whose 2-digit family matches
    the College Scorecard cip already used for breadth (REPAIR_BACKLOG #1)."""
    import json as _json
    import re

    ref = {_json.loads(line)["cip_code"] for line in open("data/reference/ref_majors.jsonl")}
    # Scorecard 4-digit families whose NCES dedicated 6-digit code lives in a
    # different family (the Scorecard aggregate is broader than the real code).
    # The program is name-aliased in field_canon, so the field signal is preserved.
    family_exceptions = {"11.08"}  # Data Science -> 30.7001 (Data Science, General)
    missing = [s for s, c in j.CIP6_BY_SLUG.items() if not c]
    assert not missing, f"programs missing cip_code: {missing[:8]}"
    for spec in j.PROGRAMS:
        slug = spec["slug"]
        cip6 = j.CIP6_BY_SLUG[slug]
        assert re.match(r"^\d{2}\.\d{4}$", cip6), f"{slug}: cip6 not 6-digit: {cip6!r}"
        assert cip6 in ref, f"{slug}: cip6 {cip6} absent from ref_majors vocabulary"
        if spec.get("cip") not in family_exceptions:
            assert cip6[:2] == (spec.get("cip") or "")[:2], (
                f"{slug}: cip6 family {cip6[:2]} != Scorecard family {spec.get('cip')}"
            )


def test_who_its_for_complete_and_program_distinct():
    """who_its_for is filled on every program and program-DISTINCT, not a
    degree-type template (REPAIR_BACKLOG #4a, miss #8 distinctness)."""
    missing = [s for s, w in j.WHO_BY_SLUG.items() if not w]
    assert not missing, f"programs missing who_its_for: {missing[:8]}"
    values = list(j.WHO_BY_SLUG.values())
    ratio = len(set(values)) / len(values)
    assert ratio >= 0.9, f"who_its_for type-gamed: distinct/total {ratio:.2f} < 0.9"


def test_graduate_tiers_carry_published_tuition():
    """Whole graduate tiers at 0% is matcher starvation — each tier must be filled."""
    from collections import Counter

    by_dt: Counter[str] = Counter()
    null_by_dt: Counter[str] = Counter()
    for spec in j.PROGRAMS:
        dt = spec["degree_type"]
        by_dt[dt] += 1
        if j._program_tuition(spec)[0] is None:
            null_by_dt[dt] += 1
    for dt in ("masters", "certificate", "professional"):
        assert null_by_dt[dt] == 0, (
            f"{dt} tier missing tuition on {null_by_dt[dt]}/{by_dt[dt]} programs"
        )
    assert null_by_dt["phd"] == 0, "PhD tier should carry tuition 0 (funded), not null"
