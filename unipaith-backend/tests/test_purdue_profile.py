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
    tuition, cost = p._program_tuition(spec)
    outcomes = dict(p._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = p._program_standard(slug, spec, tuition_omitted=tuition is None)
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
    # Breadth is asserted by per-row REALNESS, NOT a frozen padded count: when a
    # de-fabrication drops CIP-rollup / unverifiable rows the real catalog legitimately
    # SHRINKS (enrich-profile miss #2). The full rebuild (purdue_catalog.CATALOG) dropped
    # the 95 CIP×award-level certificate mints + ~16 CIP-rollup/duplicate degree rows,
    # shrinking the catalog to Purdue's real degree programs. The bar is a large, real,
    # peer-leading catalog (cf. MIT's 65) — every row a single real, distinctly-named
    # degree, enforced by the realness gates below.
    assert len(p.PROGRAMS) >= 150
    assert len(set(p.PROGRAM_SLUGS)) == len(p.PROGRAM_SLUGS)
    assert p.RANKING_DATA["ownership_type"] == "public"
    assert "public land-grant research university in west lafayette" in p.DESCRIPTION.lower()
    assert len(p.SCHOOL_OUTCOMES["campus_photos"]) >= 4


def test_no_cip_rollup_names_or_departments():
    """No program_name OR department carries an unambiguous CIP-rollup tell
    (enrich-profile miss #2): a trailing ', General'/', Other', an embedded slash, or a
    literal '(CIP NN.NN)' code. Each such row was resolved to Purdue's real degree/unit
    or dropped. (Federal comma-and lists are NOT scanned here because Purdue has real
    units with internal commas — e.g. 'Department of Speech, Language, and Hearing
    Sciences' — which were each verified individually.)
    """
    import re

    from unipaith.profile_standard.anti_stub import field_of

    def tells(text: str) -> list[str]:
        hits = []
        if re.search(r",\s*(General|Other)$", text):
            hits.append("suffix")
        if "/" in text:
            hits.append("slash")
        if re.search(r"\(CIP|\b\d\d\.\d\d\b", text):
            hits.append("cip-code")
        return hits

    bad = []
    for spec in p.PROGRAMS:
        fields = (("name", field_of(spec["program_name"])), ("dept", spec.get("department") or ""))
        for label, text in fields:
            if tells(text):
                bad.append(f"{spec['slug']} {label}={text!r}")
    assert not bad, f"CIP-rollup tells remain: {bad[:10]}"


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
        tuition, _ = p._program_tuition(spec)
        omitted = set(
            p._program_standard(spec["slug"], spec, tuition_omitted=tuition is None)["omitted"]
        )
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_graduate_tier_tuition_coverage():
    """REPAIR_BACKLOG #3/#4: graduate/professional tiers carry published tuition, and the
    matcher scalar is the NON-RESIDENT rate while ``cost_data.breakdown`` keeps BOTH rates."""
    from collections import Counter

    by_type: dict[str, list[int | None]] = {}
    for spec in p.PROGRAMS:
        dt = spec["degree_type"]
        tuition, _ = p._program_tuition(spec)
        by_type.setdefault(dt, []).append(tuition)
    assert all(t is not None for t in by_type["bachelors"])
    assert all(t is not None for t in by_type["masters"]), "master's tier must be filled"
    assert all(t is not None for t in by_type["professional"]), "professional tier must be filled"
    assert all(t == p._TUITION_GRAD_OOS for t in by_type["phd"]), (
        "PhD tier must use published nonresident graduate tuition, not a funded zero placeholder"
    )
    masters_vals = Counter(t for t in by_type["masters"] if t is not None)
    assert len(masters_vals) >= 3, "master's tier should carry distinct school differentials"
    # The matcher scalar is the NON-RESIDENT rate (#4); the CSE differential proves it.
    assert p._TUITION_GRAD_CSE_OOS in masters_vals
    assert p._TUITION_GRAD_CSE not in masters_vals, "resident rate must not be the matcher scalar"
    prof_tuition = {
        p._program_tuition(s)[0]
        for s in p.PROGRAMS
        if s["degree_type"] == "professional"
    }
    assert p._TUITION_PHARMD_OOS in prof_tuition
    assert p._TUITION_PHARMD_RESIDENT not in prof_tuition, "resident rate must not be the scalar"

    # Public-scalar invariant (#4): the matcher scalar equals the breakdown's out-of-state rate,
    # and the in-state rate is still preserved (BOTH published numbers kept, never a guess).
    for spec in p.PROGRAMS:
        scalar, cost = p._program_tuition(spec)
        breakdown = (cost or {}).get("breakdown") or {}
        assert scalar == breakdown.get("tuition_out_of_state"), (
            f"{spec['slug']}: matcher scalar must be the non-resident rate"
        )
        assert breakdown.get("tuition_in_state") is not None, (
            f"{spec['slug']}: breakdown must preserve the resident rate"
        )


def test_catalog_has_no_padding_stubs():
    """Catalog must not carry CIP×award-level padding stubs."""
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(p.PROGRAMS)
    assert not errors, f"Catalog padding detected: {errors}"
    assert all(spec.get("department") for spec in p.PROGRAMS), "every program needs a department"
    names = [spec["program_name"] for spec in p.PROGRAMS]
    assert len(names) == len(set(names)), "duplicate program_name values"


def test_flagship_programs_have_reviews():
    reviewed = [s for s in p._REVIEWS_BY_SLUG if s in p.PROGRAM_SLUGS]
    assert len(reviewed) >= 10


def test_no_name_prefixed_descriptions():
    """Gold MIT/JHU pattern — descriptions open on field facts, not program_name."""
    name_prefix = sum(
        1
        for spec in p.PROGRAMS
        if (spec.get("description") or "").startswith(spec.get("program_name", ""))
    )
    assert name_prefix == 0, f"{name_prefix} programs still prefix description with program_name"
