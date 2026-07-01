"""Boston College conforms to the gold standard across its WHOLE tree — the
institution, all eight schools, and every program — mirroring the MIT reference.

This run's repair FILLS the graduate tuition tiers (master's / professional were
matcher-blind on budget: 1/30 and 1/3) from BC's verified published per-credit
rates × published degree credits ÷ program years, and attaches gathered→cited
external_reviews to the coverable programs. The tuition-tier and reviews assertions
below lock those fixes so a later re-apply cannot silently regress them.
"""

from collections import Counter

from unipaith.data import boston_college_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.anti_stub import analyze
from unipaith.profile_standard.manifest import MANIFEST

# The single graduate program with no computable annual tuition (no fixed credit
# total → honest cost omission). Every OTHER program carries a cited tuition scalar.
_TUITION_OMIT_SLUGS = {"bc-geology-ms"}


def _required_fields_of_section(level: str, section_id: str) -> set[str]:
    sec = next(s for s in MANIFEST[level] if s.id == section_id)
    return {f.path for f in sec.fields if f.required and f.enrich}


def _gaps(level: str, res, omitted: set[str]) -> set:
    bad = set(res.missing_fields) - omitted
    for sec_id in res.missing_sections:
        if not _required_fields_of_section(level, sec_id) <= omitted:
            bad |= {f"section:{sec_id}"}
    return bad


# ── Snapshot builders — mirror _apply_* so the pure test matches persisted rows ──
def _institution_snapshot() -> dict:
    so = {**p.SCHOOL_OUTCOMES, "_standard": p._standard(p._OMITTED_INSTITUTION)}
    # campus_photos come from the bulk seed (apply() preserves them — verified live:
    # a 4-photo credited gallery); the module leaves media_gallery to the seed hero.
    return {
        "description_text": p.DESCRIPTION,
        "student_body_size": p.UNDERGRAD_COUNT,
        "media_gallery": ["https://commons.wikimedia.org/seed-hero.jpg"],
        "ranking_data": p.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": p._INSTITUTION_CONTENT,
    }


def _school_snapshot(spec: dict) -> dict:
    about = {
        **p._SCHOOL_ABOUT[spec["name"]],
        "_standard": p._standard(p._ABOUT_OMITTED.get(spec["name"], [])),
    }
    return {
        "name": spec["name"],
        "description_text": spec["description"],
        "website_url": p._SCHOOL_WEBSITE.get(spec["name"]),
        "about_detail": about,
        "content_sources": p._school_content(spec["name"]),
    }


def _cost(spec: dict) -> dict:
    grad = p._grad_cost(spec)
    if grad is not None:
        return grad
    t = p._resolve_tuition(spec)
    if t is not None:
        return {
            "tuition_usd": t,
            "funded": spec["degree_type"] == "phd",
            "source": "Boston College Office of Student Services",
            "source_url": p._TUITION_RATES_URL,
            "year": "2025-26" if spec["degree_type"] == "bachelors" else "2024-25",
        }
    return {"tuition_usd": None, "omitted_reason": p._TUITION_OMIT_REASON}


def _outcomes(spec: dict) -> dict:
    fos = p._FOS_OUTCOMES.get(spec["slug"])
    if fos is not None:
        salary, cip = fos
        o = {"median_salary": salary, "scope": "program", "cip": cip, "source": "Scorecard"}
    elif spec["degree_type"] in ("bachelors", "masters", "phd", "professional"):
        o = dict(p._OUTCOMES_INSTITUTION)
    else:
        o = {}
    o["_standard"] = p._program_standard(spec)
    return o


def _requirements(spec: dict) -> dict:
    dt = spec["degree_type"]
    if spec["school"] == p._LAW and dt == "professional":
        return dict(p._REQ_LAW)
    if spec["school"] == p._WOODS:
        return dict(p._REQ_OPEN)
    if dt == "bachelors":
        return dict(p._REQ_UNDERGRAD)
    return dict(p._REQ_GRAD)


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": spec.get("website") or p._SCHOOL_WEBSITE.get(spec["school"]),
        "department": spec.get("department"),
        "tracks": spec.get("tracks"),
        "application_requirements": _requirements(spec),
        "cost_data": _cost(spec),
        "outcomes_data": _outcomes(spec),
        "class_profile": None,
        "faculty_contacts": None,
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug),
        "content_sources": p._program_content(spec),
    }


def test_catalog_breadth_and_shape():
    assert len(p.SCHOOLS) == 8
    assert len(p.PROGRAMS) == 102
    assert len(set(p.PROGRAM_SLUGS)) == len(p.PROGRAM_SLUGS)
    assert p.RANKING_DATA["ownership_type"] == "private_nonprofit"


def test_catalog_is_anti_stub_clean():
    report = analyze(p.PROGRAMS)
    assert report.is_clean, f"anti-stub not clean: {report.summary()}"


def test_no_duplicate_rendered_name_degree():
    counts = Counter((x["program_name"], x["degree_type"]) for x in p.PROGRAMS)
    dupes = [k for k, c in counts.items() if c > 1]
    assert not dupes, f"duplicate (name, degree): {dupes}"


def test_matcher_core_cip_code_catalog_wide():
    missing = [x["slug"] for x in p.PROGRAMS if not x.get("cip")]
    assert not missing, f"programs missing cip_code: {missing[:8]}"


def test_who_its_for_is_program_distinct():
    missing = [x["slug"] for x in p.PROGRAMS if not (x.get("who") or "").strip()]
    assert not missing, f"programs missing who_its_for: {missing[:8]}"
    vals = [x.get("who") or "" for x in p.PROGRAMS]
    ratio = len(set(vals)) / max(len(vals), 1)
    assert ratio >= 0.9, f"who_its_for type-gamed: distinct/total {ratio:.2f} < 0.9"


def test_graduate_tiers_carry_published_tuition():
    """Whole master's / professional tiers at 0% is matcher starvation (skill §tuition).

    BC bills per-credit, so each grad program's scalar = published rate × credits ÷
    years. The ONLY allowed null is the credit-less Earth & Environmental Sciences M.S.,
    which is recorded as an honest omission.
    """
    null_by_dt: Counter[str] = Counter()
    null_slugs: list[str] = []
    for spec in p.PROGRAMS:
        if p._resolve_tuition(spec) is None:
            null_by_dt[spec["degree_type"]] += 1
            null_slugs.append(spec["slug"])
    assert set(null_slugs) <= _TUITION_OMIT_SLUGS, f"unexpected null tuition: {null_slugs}"
    assert null_by_dt["professional"] == 0, "professional tier missing tuition"
    # master's: only the recorded Geology omission may be null
    masters_null = [s for s in null_slugs if s not in _TUITION_OMIT_SLUGS]
    assert not masters_null, f"master's missing tuition: {masters_null}"


def test_omitted_tuition_is_recorded_with_reason():
    """A null-tuition program must record cost_data in _standard.omitted with a reason."""
    for spec in p.PROGRAMS:
        if p._resolve_tuition(spec) is None:
            omitted = p._program_standard(spec)["omitted"]
            assert "cost_data.tuition_usd" in omitted, f"{spec['slug']} null tuition not omitted"
    assert p._TUITION_OMIT_REASON  # a real reason string exists


def test_graduate_tuition_is_not_the_undergrad_sticker():
    """A grad/professional row carrying the undergraduate sticker is a copy-down defect."""
    for spec in p.PROGRAMS:
        if spec["degree_type"] in ("masters", "professional"):
            t = p._resolve_tuition(spec)
            assert t != p._BC_TUITION_UG, f"{spec['slug']} carries the undergrad sticker"


def test_coverable_programs_have_reviews():
    reviewed = [s for s in p._REVIEWS_BY_SLUG if s in p.PROGRAM_SLUGS]
    assert len(reviewed) >= 8, f"only {len(reviewed)} programs reviewed"
    for slug, rev in p._REVIEWS_BY_SLUG.items():
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]
        # cautions present — not praise-only
        assert any(t["sentiment"] in ("caution", "mixed") for t in rev["themes"]), slug
        for src in rev["sources"]:
            assert src["url"].startswith("http"), slug


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(p._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for spec in p.SCHOOLS:
        snap = _school_snapshot(spec)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{spec['name']} gaps: {bad}"
        assert snap["content_sources"], f"{spec['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in p.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(p._program_standard(spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"
