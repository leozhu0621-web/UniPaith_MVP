"""The UCSD profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 12 real schools, and every one of its programs —
mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``ucsd_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import ucsd_profile as p
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
                "source": "UC San Diego Graduate Division — Funding",
                "source_url": "https://grad.ucsd.edu/funding/",
            }
            if spec["degree_type"] == "phd"
            else {
                "note": "see program page",
                "source": "UC San Diego program tuition page",
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
    assert len(p.SCHOOLS) == 12
    assert len(p.PROGRAMS) >= 180
    assert len(set(p.PROGRAM_SLUGS)) == len(p.PROGRAM_SLUGS)
    assert p.RANKING_DATA["ownership_type"] == "public"
    assert "public research university in la jolla" in p.DESCRIPTION.lower()
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


def test_coverable_programs_have_reviews():
    """Every coverable program must EITHER carry a gathered review OR explicitly
    record external_reviews as omitted in its _standard — never a silent blank,
    and never a synthesized review. (SKILL.md miss #8: remove synthesized reviews
    and re-gather genuine program-specific coverage or omit-with-reason; an honest
    blank beats a false 'aggregated from public sources' disclaimer.)"""
    import sys

    sys.path.insert(0, "scripts")
    from fleet_audit import is_coverable

    missing = [
        spec["slug"]
        for spec in p.PROGRAMS
        if is_coverable(spec)
        and spec["slug"] not in p._REVIEWS_BY_SLUG
        and "external_reviews.summary"
        not in p._program_standard(spec["slug"], spec)["omitted"]
    ]
    assert not missing, f"Coverable programs with neither a review nor an omit: {missing}"


def test_no_name_prefixed_descriptions():
    name_prefix = sum(
        1
        for prog in p.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, f"{name_prefix} programs still prefix description with program_name"


def test_no_fabricated_units_or_shared_credential_descriptions():
    from collections import defaultdict

    for spec in p.PROGRAMS:
        assert "Center for Aerospace Research and Training" not in (
            spec.get("description") or ""
        ), spec["slug"]

    by_key: dict[tuple[str, str], list[str]] = defaultdict(list)
    for spec in p.PROGRAMS:
        fn = spec["program_name"]
        field = fn
        for prefix in (
            "Bachelor of Arts in ",
            "Bachelor of Science in ",
            "Master of Science in ",
            "Doctor of Philosophy in ",
            "Graduate Certificate in ",
        ):
            if fn.startswith(prefix):
                field = fn[len(prefix) :].strip()
                break
        by_key[(field, spec["degree_type"])].append(spec.get("description") or "")

    for key, descs in by_key.items():
        if len(descs) >= 2:
            assert len(set(descs)) == len(descs), f"shared descriptions for {key}"
