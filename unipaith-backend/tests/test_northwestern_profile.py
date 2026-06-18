"""The Northwestern profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 11 real schools, and every one of its programs —
mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``northwestern_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import northwestern_profile as n
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
    so = {**n.SCHOOL_OUTCOMES, "_standard": n._standard(n._OMITTED_INSTITUTION)}
    return {
        "description_text": n.DESCRIPTION,
        "student_body_size": n.UNDERGRAD_COUNT,
        "media_gallery": [n.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": n.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": n._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    m = next(x for x in n._SCHOOL_META if x["name"] == name)
    about = {**n._about_for(m), "_standard": n._standard(n._about_omitted(m))}
    return {
        "name": name,
        "description_text": n._school_description(m),
        "website_url": m["website"],
        "about_detail": about,
        "content_sources": n._school_content(name),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    cost = (
        {
            "tuition_usd": n._TUITION_UG,
            "total_cost_of_attendance": n._UNDERGRAD_COA,
            "avg_net_price": n._AVG_NET_PRICE,
            "funded": False,
            "source": n._COST_SRC[0],
            "source_url": n._COST_SRC[1],
        }
        if spec["degree_type"] == "bachelors"
        else (
            {
                "tuition_usd": 0,
                "funded": True,
                "source": "Northwestern The Graduate School",
                "source_url": "https://www.tgs.northwestern.edu/admission/",
            }
            if spec["degree_type"] == "phd"
            else {
                "note": "see program page",
                "source": "Northwestern program tuition page",
                "source_url": n._website_for(spec),
            }
        )
    )
    outcomes = dict(n._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = n._program_standard(slug, spec)
    kw = n._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(n._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": n._website_for(spec),
        "department": spec.get("department"),
        "tracks": n._TRACKS_BY_SLUG.get(slug),
        "application_requirements": n._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": n._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": n._FACULTY_BY_SLUG.get(slug),
        "external_reviews": n._REVIEWS_BY_SLUG.get(slug),
        "content_sources": n._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(n.SCHOOLS) == 11
    assert len(n.PROGRAMS) >= 300
    assert len(set(n.PROGRAM_SLUGS)) == len(n.PROGRAM_SLUGS)
    assert n.RANKING_DATA["ownership_type"] == "private"
    assert "private research university in evanston" in n.DESCRIPTION.lower()
    assert len(n.SCHOOL_OUTCOMES["campus_photos"]) >= 4


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(n._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for m in n._SCHOOL_META:
        snap = _school_snapshot(m["name"])
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{m['name']} gaps: {bad}"
        assert snap["content_sources"], f"{m['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in n.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(n._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_programs_have_reviews():
    reviewed = [s for s in n._REVIEWS_BY_SLUG if s in n.PROGRAM_SLUGS]
    assert len(reviewed) >= 10


def test_catalog_has_no_padding_stubs():
    """Catalog must not carry CIP×award-level padding stubs."""
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(n.PROGRAMS)
    assert not errors, f"Catalog padding detected: {errors}"
    assert all(spec.get("department") for spec in n.PROGRAMS), "every program needs a department"
    names = [spec["program_name"] for spec in n.PROGRAMS]
    assert len(names) == len(set(names)), "duplicate program_name values"


def test_no_name_prefixed_descriptions():
    name_prefix = sum(
        1
        for prog in n.PROGRAMS
        if (prog.get("description") or "").startswith(prog.get("program_name", ""))
    )
    assert name_prefix == 0, f"{name_prefix} programs still prefix description with program_name"


def test_no_peer_contaminated_descriptions():
    contaminated = sum(
        1
        for prog in n.PROGRAMS
        if any(sig in (prog.get("description") or "") for sig in n._PEER_SIGNATURES)
    )
    assert contaminated == 0, f"{contaminated} programs still carry peer-institution signatures"


def test_no_identical_across_credential_levels():
    from collections import Counter

    desc_counts = Counter(prog.get("description") for prog in n.PROGRAMS)
    shared = sum(c for c in desc_counts.values() if c >= 2)
    assert shared == 0, (
        f"{shared} programs share a description verbatim with a credential sibling"
    )


# --- Anti-synthesized-review gate (SKILL.md miss #8: fabrication-by-synthesis) ---
# A review ships ONLY when it is hand-gathered from program-specific coverage. A
# batch minted one-per-row from (program_name, school, institution rank) leaves two
# machine fingerprints these tests block so a future one-sweep re-mint FAILS CI:
#   (1) the SAME theme detail copy-pasted across many programs, and
#   (2) a single institution-level source cited on a large share of reviews.
# (The 48-row ``DEPTH_REVIEWS`` batch removed in northwesternprof7 had a theme
# repeated 13–15x and a bare "U.S. News — Northwestern University" source on 37 rows.)

_REVIEWED = {s: r for s, r in n._REVIEWS_BY_SLUG.items() if s in n.PROGRAM_SLUGS}


def test_reviews_only_on_real_non_rollup_programs():
    name_by_slug = {p["slug"]: p["program_name"] for p in n.PROGRAMS}
    rollup_tells = (", General", ", Other", ", and ", " Other")
    offenders = [
        name_by_slug[s]
        for s in _REVIEWED
        if any(t in name_by_slug[s] for t in rollup_tells)
    ]
    assert not offenders, f"reviews attached to CIP-rollup program names: {offenders}"


def test_no_synthesized_review_theme_reuse():
    from collections import Counter

    theme_ct: Counter = Counter()
    for r in _REVIEWED.values():
        # de-dup within one review, then count cross-program reuse
        for detail in {t["detail"] for t in r.get("themes", [])}:
            theme_ct[detail] += 1
    reused = {d: c for d, c in theme_ct.items() if c >= 3}
    assert not reused, (
        "theme detail copy-pasted across >=3 programs (synthesis tell): "
        f"{ {d[:60]: c for d, c in reused.items()} }"
    )


def test_no_institution_source_monoculture():
    from collections import Counter

    src_ct: Counter = Counter()
    for r in _REVIEWED.values():
        for src in {s["label"] for s in r.get("sources", [])}:
            src_ct[src] += 1
    # genuine flagship reviews share at most an institution Niche page a few times;
    # a synthesized batch cites one institution ranking on dozens of rows.
    overused = {label: c for label, c in src_ct.items() if c >= 8}
    assert not overused, (
        f"a single source cited on >=8 reviews (synthesis tell): {overused}"
    )


def test_no_synthesized_depth_reviews_module():
    # The machine-synthesized batch lived in this module; it must stay gone so a
    # future "complete coverable reviews 55/55" pass cannot silently re-add it.
    import importlib

    import pytest

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("unipaith.data.northwestern_reviews_depth")
