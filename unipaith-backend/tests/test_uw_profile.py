"""The UW profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 16 real colleges/schools (plus the interdisciplinary
Graduate School), and every one of its programs — mirroring the MIT/Sloan/MBAn
reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``uw_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import uw_profile as u
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
    so = {**u.SCHOOL_OUTCOMES, "_standard": u._standard(u._OMITTED_INSTITUTION)}
    return {
        "description_text": u.DESCRIPTION,
        "student_body_size": u.UNDERGRAD_COUNT,
        "media_gallery": [u.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": u.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": u._INSTITUTION_CONTENT,
    }


def _school_snapshot(m: dict) -> dict:
    about = {**u._about_for(m), "_standard": u._standard(u._about_omitted(m))}
    return {
        "name": m["name"],
        "description_text": u._school_description(m),
        "website_url": m["website"],
        "about_detail": about,
        "content_sources": u._school_content(m["name"]),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    is_ug = spec["degree_type"] == "bachelors"
    cost = u._undergrad_cost(spec) if is_ug else u._grad_cost(spec)
    outcomes = dict(u._OUTCOMES_BY_SLUG.get(slug, {}))
    outcomes["_standard"] = u._program_standard(slug, spec)
    kw = u._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(u._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": u._website_for(spec),
        "department": spec.get("department"),
        "tracks": u._TRACKS_BY_SLUG.get(slug),
        "application_requirements": u._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": u._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": u._FACULTY_BY_SLUG.get(slug),
        "external_reviews": u._REVIEWS_BY_SLUG.get(slug),
        "content_sources": u._program_content(spec["school"], kw),
        "who_its_for": u._WHO_BY_SLUG.get(slug),
    }


def test_who_its_for_complete_and_program_distinct():
    # REPAIR_BACKLOG #3 — who_its_for is filled on EVERY program (no hard-null) AND is
    # PROGRAM-DISTINCT (not a degree-type template): distinct/total ≈ 1.0.
    missing = [s for s in u.PROGRAM_SLUGS if not (u._WHO_BY_SLUG.get(s) or "").strip()]
    assert not missing, f"who_its_for missing on {len(missing)} rows: {missing[:5]}"
    vals = [v.strip() for v in u._WHO_BY_SLUG.values()]
    ratio = len(set(vals)) / len(vals)
    assert ratio >= 0.9, f"who_its_for not program-distinct: {ratio:.2f}"
    # never a hard-null in apply() — the regression that shipped the field 0% live
    import inspect

    src = inspect.getsource(u.apply) + inspect.getsource(u._apply_programs)
    assert "who_its_for = None" not in src, "who_its_for must not be hard-nulled in apply()"


def test_catalog_breadth_and_shape():
    # Full published degree catalog across UW's 16 colleges/schools + Graduate School.
    assert len(u.SCHOOLS) == 16
    assert len(u.PROGRAMS) >= 355
    assert len(set(u.PROGRAM_SLUGS)) == len(u.PROGRAM_SLUGS)
    # online delivery is set on UW's PCE online degrees
    assert sum(1 for p in u.PROGRAMS if p["delivery_format"] == "online") >= 4
    # professional doctorates (MD/DDS/JD/PharmD/DNP/DPT/AuD) are in the catalog
    assert sum(1 for p in u.PROGRAMS if p["degree_type"] == "professional") >= 5
    # ownership + classification drive the explore-card eyebrow
    assert u.RANKING_DATA["ownership_type"] == "public"
    assert "public research university in seattle" in u.DESCRIPTION.lower()
    assert "washington.edu/news/feed/" in u._INSTITUTION_CONTENT["news_rss"]
    # De-fabrication: no school-blurb stubs; real owning school in department
    assert not any("connects to" in (p.get("description") or "") for p in u.PROGRAMS)
    assert not any("Students build depth" in (p.get("description") or "") for p in u.PROGRAMS)
    assert all(p.get("department") == p["school"] for p in u.PROGRAMS)


def test_catalog_descriptions_are_field_specific_and_real():
    from unipaith.profile_standard.anti_stub import analyze

    report = analyze(u.PROGRAMS)
    assert report.is_clean, f"UW catalog is not anti-stub clean: {report.summary()}"


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(u._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"
    assert "school_outcomes.test_scores" in u._OMITTED_INSTITUTION


def test_every_school_is_conformant():
    for m in u._SCHOOL_META:
        snap = _school_snapshot(m)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{m['name']} gaps: {bad}"
        assert snap["content_sources"], f"{m['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in u.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(u._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def test_flagship_programs_carry_reviews():
    # Beat the "1 reviewed program" bug: coverable flagships carry external_reviews.
    for slug in (
        "uw-computer-science-bs",
        "uw-computer-science-and-engineering-ms",
        "uw-medicine-prof",
        "uw-nursing-practice-prof",
        "uw-library-and-information-science-ms",
        "uw-business-administration-ms",
        "uw-law-prof",
        "uw-pharmacy-prof",
        "uw-social-work-ms",
        "uw-bioengineering-ms",
        "uw-statistics-bs",
    ):
        assert slug in u._REVIEWS_BY_SLUG, f"{slug} should carry external_reviews"
        rev = u._REVIEWS_BY_SLUG[slug]
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]


# The ONLY two programs whose tuition is honestly omitted-with-reason rather than carrying a
# wrong value: the Doctor of Audiology (variable graduate-tier schedule, no single published
# annual figure) and the online BA in Integrated Social Sciences (a per-credit degree-completion
# program with no fixed credits-to-degree total). Every OTHER program — including the 14 fee-based
# / self-sustaining programs, which publish their own residency-independent per-credit rate — must
# carry a published rate (REPAIR_BACKLOG #1: a knowable matcher-core field is not an omission).
_TUITION_OMITTED_SLUGS = {"uw-audiology-prof", "uw-integrated-social-sciences-bs"}


def test_matcher_core_tuition_is_published_catalog_wide():
    """REPAIR_BACKLOG #1/#4: the catalog must not ship a matcher-core tuition null the
    institution publishes. Every program carries a published annual tuition except the two
    honestly-omitted programs, so the matcher reads a real budget signal for the rest.
    """
    missing = [
        spec["slug"]
        for spec in u.PROGRAMS
        if u._tuition_for(spec) is None and spec["slug"] not in _TUITION_OMITTED_SLUGS
    ]
    assert not missing, f"programs missing published tuition: {missing[:8]}"
    # Exactly the two recorded omissions carry a null — each recorded in _standard.omitted.
    nulls = {spec["slug"] for spec in u.PROGRAMS if u._tuition_for(spec) is None}
    assert nulls == _TUITION_OMITTED_SLUGS, f"unexpected tuition nulls: {nulls ^ _TUITION_OMITTED_SLUGS}"  # noqa: E501
    for spec in u.PROGRAMS:
        if u._tuition_for(spec) is None:
            omitted = u._program_standard(spec["slug"], spec)["omitted"]
            assert "cost_data.tuition_usd" in omitted


def test_fee_based_programs_carry_flat_published_tuition():
    """REPAIR_BACKLOG #1: the 14 fee-based / self-sustaining programs each publish a
    residency-independent per-credit rate, so a real annual figure is knowable and must be
    stamped (never a matcher-blind null). The rate is flat, so the in-state and out-of-state
    breakdown values are equal (no resident/non-resident split), and the cost record cites the
    program's own published cost page."""
    by_slug = {p["slug"]: p for p in u.PROGRAMS}
    assert u._FEE_BASED_TUITION, "no fee-based tuition map"
    for slug in u._FEE_BASED_TUITION:
        assert slug in by_slug, f"fee-based slug not in catalog: {slug}"
        spec = by_slug[slug]
        annual = u._tuition_for(spec)
        assert isinstance(annual, int) and annual > 0, f"{slug}: no positive annual tuition"
        cost = u._undergrad_cost(spec) if spec["degree_type"] == "bachelors" else u._grad_cost(spec)
        assert cost.get("tuition_usd") == annual, f"{slug}: cost card tuition != scalar"
        bd = cost.get("breakdown", {})
        assert bd.get("tuition_in_state") == bd.get("tuition_out_of_state") == annual, (
            f"{slug}: fee-based breakdown must be flat (residency-independent)"
        )
        assert cost.get("source_url", "").startswith("http"), f"{slug}: missing cited source_url"


def test_no_undergrad_sticker_copydown():
    """A graduate/professional row carrying the undergraduate sticker is the BU/Cornell
    copy-down defect — the matcher would score the same budget for a funded PhD and a
    professional degree. UW's graduate sticker is distinct from the undergrad one. The
    guard checks the exposed undergrad scalar (the non-resident sticker, REPAIR_BACKLOG #2)."""
    for ug in (u._TUITION_UG_NONRES, u._TUITION_UG_RESIDENT):
        copydown = [
            spec["slug"]
            for spec in u.PROGRAMS
            if spec["degree_type"] != "bachelors" and u._tuition_for(spec) == ug
        ]
        assert not copydown, f"undergrad sticker copied onto graduate rows: {copydown[:8]}"


def test_matcher_core_cip_code_catalog_wide():
    """REPAIR_BACKLOG #1: cip_code is the CIP join key the CPEF matcher uses to resolve a
    program's field to ref_majors + the field-66 vocabulary. A null leaves the catalog
    field-blind. Every program must carry a valid CIP-2020 4-digit code."""
    import re

    missing = [spec["slug"] for spec in u.PROGRAMS if not spec.get("cip")]
    assert not missing, f"programs missing cip_code: {missing[:8]}"
    bad = sorted({p["cip"] for p in u.PROGRAMS if not re.fullmatch(r"\d{2}\.\d{4}", p["cip"])})
    assert not bad, f"malformed cip_code values: {bad}"


def test_public_tuition_scalar_is_nonresident():
    """REPAIR_BACKLOG #2: UW is public, so the matcher's flat ``program.tuition`` scalar (set by
    ``_tuition_for``) must carry the NON-RESIDENT sticker — the out-of-state + international pool
    is scored on it. The editorial cost card stays on the coherent WA-resident basis
    (``cost_data.tuition_usd`` == resident, matching the resident COA), with BOTH rates always in
    ``cost_data.breakdown``."""
    # Bachelor's matcher scalar is the non-resident undergraduate sticker (not the resident one).
    bachelors = [s for s in u.PROGRAMS if s["degree_type"] == "bachelors" and u._tuition_for(s)]
    assert bachelors, "expected on-campus bachelor's rows"
    assert all(u._tuition_for(s) == u._TUITION_UG_NONRES for s in bachelors)
    assert u._TUITION_UG_NONRES > u._TUITION_UG_RESIDENT
    # On-campus master's/PhD matcher scalar is the non-resident graduate Tier I sticker.
    grad = [
        s
        for s in u.PROGRAMS
        if s["degree_type"] in {"masters", "phd"} and s.get("delivery_format") != "online"
    ]
    assert all(u._tuition_for(s) == u._TUITION_GRAD_NONRES for s in grad)
    assert u._TUITION_GRAD_NONRES > u._TUITION_GRAD_RESIDENT
    # cost_data shows the coherent resident basis; the breakdown preserves BOTH rates, and the
    # resident headline never exceeds the resident COA (the P2 coherence guard).
    ug = u._undergrad_cost({"degree_type": "bachelors"})
    assert ug["tuition_usd"] == u._TUITION_UG_RESIDENT
    assert ug["tuition_usd"] <= ug["total_cost_of_attendance"]
    assert ug["breakdown"]["tuition_in_state"] == u._TUITION_UG_RESIDENT
    assert ug["breakdown"]["tuition_out_of_state"] == u._TUITION_UG_NONRES
    gr = u._grad_cost({"degree_type": "masters"})
    assert gr["tuition_usd"] == u._TUITION_GRAD_RESIDENT
    assert gr["breakdown"]["tuition_in_state"] == u._TUITION_GRAD_RESIDENT
    assert gr["breakdown"]["tuition_out_of_state"] == u._TUITION_GRAD_NONRES
    # Professional rows: matcher scalar = non-resident; card shows resident; both in breakdown.
    law = next(s for s in u.PROGRAMS if s["slug"] == "uw-law-prof")
    assert u._tuition_for(law) == 58956
    law_cost = u._grad_cost(law)
    assert law_cost["tuition_usd"] == 47073
    assert law_cost["breakdown"]["tuition_in_state"] == 47073
    assert law_cost["breakdown"]["tuition_out_of_state"] == 58956


def test_graduate_tiers_carry_published_tuition():
    """A whole graduate tier at 0% is matcher starvation the aggregate hides — each tier
    is filled (PhD carries the published grad sticker, funding being a separate signal)."""
    from collections import Counter

    # Among state-supported (non-online) programs, every graduate tier is fully covered;
    # fee-based online programs are omitted-with-reason and counted separately.
    null_by_dt: Counter[str] = Counter()
    for spec in u.PROGRAMS:
        if u._tuition_for(spec) is None and spec.get("delivery_format") != "online":
            null_by_dt[spec["degree_type"]] += 1
    assert null_by_dt["masters"] == 0, "on-campus master's tier must be fully covered"
    assert null_by_dt["phd"] == 0, "PhD tier must carry the published grad sticker, not null"
    # Professional: only the Doctor of Audiology is omitted-with-reason.
    assert null_by_dt["professional"] == 1
