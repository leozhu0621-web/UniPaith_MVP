"""Case Western Reserve University conforms to the gold standard across its WHOLE
tree — the institution, all eight degree-granting schools, and every program —
mirroring the MIT reference.

This is a bare-seed enrichment (0 programs → a real, bulletin-verified 206-program
catalog across CWRU's eight schools) plus matcher-core tuition / cip_code /
program-distinct who_its_for, working feeds, and gathered→cited external_reviews on
six coverable flagships. The assertions below lock the structure, anti-stub cleanliness,
matcher-core coverage, and per-tier tuition realness so a later re-apply cannot regress them.
"""

# ruff: noqa: E501

from collections import Counter

from unipaith.data import case_western_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.anti_stub import analyze
from unipaith.profile_standard.manifest import MANIFEST

# Programs whose per-program tuition CWRU does not publish in a verifiable form → the
# annual scalar is an honest cost omission (postdoctoral M.S.D. dental specialties, the
# PA program's fees-blended figure, Weatherhead MBAI/MSLOC, and the specialized non-J.D./
# LL.M. School of Law master's). Every OTHER program carries a cited tuition scalar.
_TUITION_OMIT_SLUGS = set(p._TUITION_OMIT)


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


def _outcomes(spec: dict) -> dict:
    fos = p._FOS_OUTCOMES.get(spec["slug"])
    if fos is not None:
        salary, cip = fos
        o = {"median_salary": salary, "scope": "program", "cip": cip, "source": "Scorecard"}
    else:
        o = dict(p._OUTCOMES_INSTITUTION)
    o["_standard"] = p._program_standard(spec)
    return o


def _requirements(spec: dict) -> dict:
    dt = spec["degree_type"]
    if spec["school"] == p._LAW and dt == "professional":
        return dict(p._REQ_LAW)
    if spec["school"] in (p._MED, p._DENT) and dt == "professional":
        return dict(p._REQ_MED)
    if dt == "bachelors":
        return dict(p._REQ_UNDERGRAD)
    return dict(p._REQ_GRAD)


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": spec.get("website") or p._SCHOOL_WEBSITE.get(spec["school"]),
        "department": spec.get("department"),
        "tracks": spec.get("tracks"),
        "application_requirements": _requirements(spec),
        "cost_data": p._cost_data(spec),
        "outcomes_data": _outcomes(spec),
        "class_profile": None,
        "faculty_contacts": None,
        "external_reviews": p._REVIEWS_BY_SLUG.get(slug),
        "content_sources": p._program_content(spec),
    }


def test_catalog_breadth_and_shape():
    assert len(p.SCHOOLS) == 8
    assert len(p.PROGRAMS) == 206
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


def test_descriptions_non_empty_and_no_prefix_double():
    empty = [x["slug"] for x in p.PROGRAMS if not (x["description"] or "").strip()]
    assert not empty, f"empty descriptions: {empty[:8]}"
    doubled = [x["slug"] for x in p.PROGRAMS if x["description"].startswith(x["program_name"])]
    assert not doubled, f"description doubles the program name: {doubled[:8]}"


def test_graduate_tiers_carry_published_tuition():
    """Bachelor's ~100%, PhD funded (0), master's/professional tiers majority-covered.

    A whole tier at 0% would be matcher starvation; the only null-tuition programs are
    those CWRU does not publish in a verifiable form, all recorded omitted-with-reason.
    """
    null_slugs = [s["slug"] for s in p.PROGRAMS if p._cost_data(s).get("tuition_usd") is None]
    assert set(null_slugs) <= _TUITION_OMIT_SLUGS, f"unexpected null tuition: {set(null_slugs) - _TUITION_OMIT_SLUGS}"
    by_dt: Counter[str] = Counter()
    filled_by_dt: Counter[str] = Counter()
    for s in p.PROGRAMS:
        by_dt[s["degree_type"]] += 1
        if p._cost_data(s).get("tuition_usd") is not None:
            filled_by_dt[s["degree_type"]] += 1
    assert filled_by_dt["bachelors"] == by_dt["bachelors"], "bachelor's tier must be 100% covered"
    assert filled_by_dt["phd"] == by_dt["phd"], "phd tier ships funded tuition=0 (non-null)"
    # master's / professional tiers must be majority-covered (no whole-tier starvation)
    assert filled_by_dt["masters"] / by_dt["masters"] >= 0.8, "master's tier under-covered"
    assert filled_by_dt["professional"] / by_dt["professional"] >= 0.8, "professional tier under-covered"


def test_omitted_tuition_is_recorded_with_reason():
    for spec in p.PROGRAMS:
        if p._cost_data(spec).get("tuition_usd") is None:
            omitted = p._program_standard(spec)["omitted"]
            assert "cost_data.tuition_usd" in omitted, f"{spec['slug']} null tuition not omitted"
            assert p._TUITION_OMIT.get(spec["slug"]), f"{spec['slug']} missing omit reason"


def test_graduate_tuition_is_not_the_undergrad_sticker():
    """A grad/professional row carrying the undergraduate sticker is a copy-down defect."""
    for spec in p.PROGRAMS:
        if spec["degree_type"] in ("masters", "professional"):
            t = p._cost_data(spec).get("tuition_usd")
            assert t != p._TUITION_UG, f"{spec['slug']} carries the undergrad sticker"


def _domain(url: str) -> str:
    return url.split("/")[2].replace("www.", "")


def test_coverable_programs_have_reviews():
    reviewed = [s for s in p._REVIEWS_BY_SLUG if s in p.PROGRAM_SLUGS]
    assert len(reviewed) >= 4, f"only {len(reviewed)} programs reviewed"
    for slug, rev in p._REVIEWS_BY_SLUG.items():
        assert slug in p.PROGRAM_SLUGS, f"review for unknown slug: {slug}"
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]
        assert any(t["sentiment"] in ("caution", "mixed") for t in rev["themes"]), slug
        for src in rev["sources"]:
            assert src["url"].startswith("http"), slug
        # authoritative_2x: >= 2 INDEPENDENT (non-case.edu) source domains.
        indep = {_domain(s["url"]) for s in rev["sources"] if "case.edu" not in _domain(s["url"])}
        assert len(indep) >= 2, f"{slug} lacks 2 independent source domains: {indep}"


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
