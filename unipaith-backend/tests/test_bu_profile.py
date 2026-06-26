"""The BU profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 22 real schools/colleges, and every one of its
programs — mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``bu_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes
when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from unipaith.data import bu_profile as b
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST

_COVERABLE_REVIEWS = {
    "bu-academics-cas-computer-science-ba",
    "bu-academics-cds-bs-in-data-science",
    "bu-academics-questrom-mba",
    "bu-academics-law-jd",
    "bu-academics-busm-four-year-program",
    "bu-academics-sdm-doctor-of-dental-medicine",
    "bu-academics-sph-mph",
    "bu-academics-ssw-clinical-social-work-practice",
    "bu-academics-eng-electrical-engineering-bs",
    "bu-academics-com-journalism-bs",
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration",
    "bu-academics-cas-international-relations-ba",
    "bu-academics-com-film-television-film-televisionbs",
    "bu-academics-eng-biomedical-engineering-bs",
    "bu-academics-questrom-ms-in-business-analytics",
    "bu-academics-questrom-ms-in-finance",
    "bu-academics-questrom-mathematical-finance-ms",
    "bu-academics-cds-ms-in-data-science",
    "bu-academics-met-computer-science-ms",
    "bu-academics-met-computer-science-master-of-science-in-applied-data-analytics",
    "bu-academics-eng-computer-engineering-bs",
    "bu-academics-eng-mechanical-engineering-bs",
    "bu-academics-cas-economics-ba",
    "bu-academics-cas-physics-ba",
    "bu-academics-cas-chemistry-ba",
    "bu-academics-cas-psychology-ba",
    "bu-academics-com-journalism-ms",
    "bu-academics-sha-ms",
    "bu-academics-ssw-msw",
    "bu-academics-sph-mba-mph",
    "bu-academics-busm-combined-md-mba",
    "bu-academics-eng-computer-engineering-ms",
    "bu-academics-cas-mathematics-statistics-ba",
    "bu-academics-met-computer-science-bs",
}


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
    so = {**b.SCHOOL_OUTCOMES, "_standard": b._standard(b._OMITTED_INSTITUTION)}
    return {
        "description_text": b.DESCRIPTION,
        "student_body_size": b.UNDERGRAD_COUNT,
        "media_gallery": [b.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": b.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": b._INSTITUTION_CONTENT,
    }


def _school_snapshot(m: dict) -> dict:
    about = {**b._about_for(m), "_standard": b._standard(b._about_omitted(m))}
    return {
        "name": m["name"],
        "description_text": b._school_description(m),
        "website_url": m["website"],
        "about_detail": about,
        "content_sources": b._school_content(m["name"]),
    }


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    _, cost = b._program_tuition(spec)
    outcomes = dict(b._OUTCOMES_BY_SLUG.get(slug, {}))
    outcomes["_standard"] = b._program_standard(slug, spec)
    kw = b._PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(b._KEYWORDS_BY_SCHOOL[spec["school"]])
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "on_campus"),
        "description_text": spec["description"],
        "website_url": b._website_for(spec),
        "department": spec.get("department"),
        "tracks": spec.get("tracks"),
        "application_requirements": b._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": b._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": b._FACULTY_BY_SLUG.get(slug),
        "external_reviews": b._REVIEWS_BY_SLUG.get(slug),
        "content_sources": b._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    assert len(b.SCHOOLS) == 22
    # After concentration-split collapse (miss #2), the real catalog is ~360 distinct degrees.
    assert len(b.PROGRAMS) >= 300
    assert len(set(b.PROGRAM_SLUGS)) == len(b.PROGRAM_SLUGS)
    assert sum(1 for p in b.PROGRAMS if p["delivery_format"] == "online") >= 20
    assert sum(1 for p in b.PROGRAMS if p["degree_type"] == "professional") >= 5
    assert sum(1 for p in b.PROGRAMS if p.get("tracks")) >= 30
    assert b.RANKING_DATA["ownership_type"] == "private"
    assert "private research university in boston" in b.DESCRIPTION.lower()
    assert len(b.SCHOOL_OUTCOMES["campus_photos"]) >= 4
    assert "bu.edu/buniverse" in b._INSTITUTION_CONTENT["news_rss"]


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(b._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"


def test_every_school_is_conformant():
    for m in b._SCHOOL_META:
        snap = _school_snapshot(m)
        res = check_conformance("school", snap, profile_version=STANDARD_VERSION)
        omitted = set((snap["about_detail"] or {}).get("_standard", {}).get("omitted", []))
        bad = _gaps("school", res, omitted)
        assert not bad, f"{m['name']} gaps: {bad}"
        assert snap["content_sources"], f"{m['name']} missing content_sources"


def test_every_program_is_conformant_or_omitted():
    for spec in b.PROGRAMS:
        snap = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        omitted = set(b._program_standard(spec["slug"], spec)["omitted"])
        bad = _gaps("program", res, omitted)
        assert not bad, f"{spec['slug']} has un-omitted gaps: {bad}"
        assert snap["content_sources"], f"{spec['slug']} missing content_sources"


def _resolved_slug(slug: str) -> str:
    return b._SLUG_REDIRECT.get(slug, slug)


def test_flagship_programs_have_reviews():
    for slug in _COVERABLE_REVIEWS:
        resolved = _resolved_slug(slug)
        assert resolved in b._REVIEWS_BY_SLUG, f"{slug} -> {resolved}"
        assert b._REVIEWS_BY_SLUG[resolved].get("summary"), resolved
        assert len(b._REVIEWS_BY_SLUG[resolved].get("sources", [])) >= 2, resolved


def test_catalog_has_no_padding_stubs():
    """Catalog must not carry bare-abbr / CIP×award-level padding stubs."""
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(b.PROGRAMS)
    assert not errors, f"Catalog padding detected: {errors}"


def _field_of(name: str) -> str:
    """The field-of-study portion of a program name (strip the credential designation)."""
    import re

    head = name.split(" / ")[0]
    return re.sub(r"^.*? in ", "", head).strip() if " in " in head else head


def test_no_department_is_a_bare_field_echo():
    """The department must be the real owning school/college, NEVER the field echoed
    verbatim from the program name (miss #2 dept-echo — the BU CRITICAL #1 defect: 216
    rows once set department == the field, e.g. 'Bachelor of Arts in Anthropology' ->
    'Anthropology', while the real owning College of Arts & Sciences was known). Gold MIT
    scores 0 here; so must BU."""
    echoes = [
        (p["program_name"], p["department"])
        for p in b.PROGRAMS
        if p.get("department") and p["department"] == _field_of(p["program_name"])
    ]
    assert not echoes, f"department echoes the name's field on {len(echoes)} rows: {echoes[:8]}"


def test_no_literal_minor_stub_names():
    """No program may ship the literal stub name 'minor' (REPAIR BACKLOG #10)."""
    stubs = [p["slug"] for p in b.PROGRAMS if (p.get("program_name") or "").lower() == "minor"]
    assert not stubs, f"literal 'minor' stub names: {stubs}"


def test_no_identical_across_credential_levels():
    from collections import Counter

    desc_counts = Counter(prog.get("description") for prog in b.PROGRAMS)
    shared = sum(c for c in desc_counts.values() if c >= 2)
    assert shared == 0, (
        f"{shared} programs share a description verbatim with a credential sibling"
    )


def test_catalog_is_anti_stub_clean():
    """Per-credential bodies — gold MIT = 0% frame-stripped shared body (REPAIR HIGH #5)."""
    from unipaith.profile_standard.anti_stub import (
        analyze,
        frame_stripped_shared_body,
        scrape_debris,
    )

    report = analyze(b.PROGRAMS)
    assert report.is_clean, f"anti-stub not clean: {report.summary()}"
    shared = frame_stripped_shared_body(b.PROGRAMS, abs_chars=150)
    assert not shared, (
        f"credential siblings share a 150+-char body on "
        f"{len(shared)} field(s): {shared[:8]}"
    )
    assert not scrape_debris(b.PROGRAMS), "un-terminated or debris descriptions"


def test_matcher_core_tuition_is_value_correct():
    """Tuition is VALUE-correct, not merely present (REPAIR_BACKLOG run 75 HIGH #1: the
    undergrad sticker must NOT be copied down onto graduate rows). BU charges ONE flat
    full-time rate ($69,870) for undergraduate AND most full-time graduate/professional
    programs — a VERIFIED BU policy (BU Student Financials + U.S. News for the Questrom MBA),
    so a general full-time graduate row at $69,870 is its real published rate, not a copy-down.
    Invariants:
      * funded research doctorates (PhD/DSc) and per-credit graduate certificates carry NO
        flat tuition — they are recorded as honest omissions. EXCEPTION: the Goldman SDM
        postdoctoral / advanced-education clinical specialties (endodontics, periodontology,
        etc.) publish ONE uniform annual rate ($101,630, BUMC OSFS) across their certificate /
        master's / clinical-doctorate tiers and are billed (not funded), so they carry that
        verified published rate (REPAIR_BACKLOG #3) — never the undergrad sticker;
      * schools with a DISTINCT published rate stamp it, never the undergrad sticker;
      * every program with tuition None records cost_data.tuition_usd in _standard.omitted and
        carries a cost_data explanation.
    """
    ug = b._TUITION_UG
    for spec in b.PROGRAMS:
        tuition, cost = b._program_tuition(spec)
        dt = spec["degree_type"]
        is_sdm = spec.get("school_key") == "SDM"
        assert cost and cost.get("note") and cost.get("source"), f"{spec['slug']} cost incomplete"
        # Funded research doctorates + per-credit certificates ship no flat number — except
        # the billed Goldman SDM postdoctoral specialties, which publish a flat annual rate.
        if (dt in ("phd", "doctoral") or dt == "certificate") and not is_sdm:
            assert tuition is None, f"{spec['slug']}: {dt} should be omitted, got {tuition}"
        if is_sdm and dt != "professional":
            assert tuition == b._SDM_POSTDOC_TUITION, (
                f"{spec['slug']}: SDM advanced-education should carry the published "
                f"postdoctoral rate {b._SDM_POSTDOC_TUITION}, got {tuition}"
            )
        if tuition is None:
            omitted = b._program_standard(spec["slug"], spec)["omitted"]
            assert "cost_data.tuition_usd" in omitted, f"{spec['slug']} omission not recorded"
    # No certificate / phd row carries the undergrad sticker (the run-75 copy-down defect).
    copydown = [
        p["slug"]
        for p in b.PROGRAMS
        if p["degree_type"] in ("certificate", "phd", "doctoral")
        and b._program_tuition(p)[0] == ug
    ]
    assert not copydown, f"undergrad sticker copied onto funded/per-credit rows: {copydown[:8]}"
    # Professional doctorates carry their own published rates (distinct from the UG sticker).
    md = [b._program_tuition(p)[0] for p in b.PROGRAMS if p["program_name"] == "Doctor of Medicine"]
    assert md and all(t == b._MD_TUITION for t in md), f"MD rate wrong: {md}"
    dmd = [
        b._program_tuition(p)[0]
        for p in b.PROGRAMS
        if p["program_name"] == "Doctor of Dental Medicine"
    ]
    assert dmd and all(t == b._DMD_TUITION for t in dmd), f"DMD rate wrong: {dmd}"
    # Distinct graduate rates appear across the master's tier (the copy-down is broken up).
    masters_vals = {b._program_tuition(p)[0] for p in b.PROGRAMS if p["degree_type"] == "masters"}
    for rate in (40352, 24648, 30376, 34984):
        assert rate in masters_vals, f"distinct grad rate {rate} missing"
    # The bachelor's tier is the published full-time rate, catalog-wide.
    assert all(
        b._program_tuition(p)[0] == ug for p in b.PROGRAMS if p["degree_type"] == "bachelors"
    )


def test_no_concentration_split_rows():
    """No program_name may carry a '{degree} — {concentration}' tail (miss #2): a degree's
    concentrations belong in its ``tracks``, not as separate name-suffixed rows. The two true
    concentration splits (GRS M.S. in CS — Artificial Intelligence; JD/MBA — Health Sector
    Management) are collapsed into the keeper's tracks; the rest were renamed to clean,
    school/delivery-distinguished names. Gold MIT scores 0 here."""
    split = [p["program_name"] for p in b.PROGRAMS if " — " in p["program_name"]]
    assert not split, f"concentration-split / em-dash names remain: {split}"


def test_force_collapsed_rows_dropped_and_tracks_merged():
    """The two collapsed concentration rows are dropped and their concentration lands on the
    keeper's tracks (miss #2)."""
    slugs = {p["slug"] for p in b.PROGRAMS}
    for dropped, (keeper, track) in b._FORCE_COLLAPSE.items():
        assert dropped not in slugs, f"{dropped} should be collapsed away"
        krow = next((p for p in b.PROGRAMS if p["slug"] == keeper), None)
        assert krow is not None, f"keeper {keeper} missing"
        assert track in (krow.get("tracks") or []), (
            f"{track!r} not merged into {keeper} tracks {krow.get('tracks')!r}"
        )


def test_no_credential_combo_names_or_departments():
    """No program_name or department may be a bare/mechanical credential-combo token —
    'Jdma English', 'Jdllm In Finance', 'PhD, MD/PhD' (miss #2). Real joint degrees carry
    their full designation ('Juris Doctor / Master of Arts in English')."""
    import re

    bad_token = re.compile(r"^(Jd|Jdma|Jdllm|Mdjd|Mdphd|Md|Mph|Phd|PhD,|Llm|Ba|Bs|Ma|Ms)\b")
    bad = [
        (p["program_name"], p.get("department"))
        for p in b.PROGRAMS
        if bad_token.match(p["program_name"])
        or (p.get("department") and bad_token.match(p["department"]))
    ]
    assert not bad, f"credential-combo stub names/departments: {bad}"


def test_cip_code_is_complete():
    """Matcher-core cip_code (REPAIR_BACKLOG #1): every program resolves to a verified NCES
    CIP family via bu_cip_who (was null fleet-wide → matcher field-blind). No row may ship
    without a code — the build gate in bu_profile already raises on any uncovered row, so a
    full assignment here proves 100% coverage from the same source apply() stamps."""
    uncovered = [s["slug"] for s in b.PROGRAMS if not b._CIP_BY_SLUG.get(s["slug"])]
    assert not uncovered, f"cip_code uncovered on {len(uncovered)} rows: {uncovered[:8]}"
    assert len(b._CIP_BY_SLUG) == len(b.PROGRAMS)
    import re

    bad = [c for c in b._CIP_BY_SLUG.values() if not re.fullmatch(r"\d\d\.\d{2,4}", c)]
    assert not bad, f"malformed CIP codes: {bad[:8]}"


def test_who_its_for_is_complete_and_distinct():
    """who_its_for (REPAIR_BACKLOG #4a) is a universal depth field — every program carries a
    field-specific statement, and the set is program-DISTINCT (NOT a one-per-degree-type
    template). distinct/total must approach 1.0 (Cornell's bar); never collapse to ~0.1."""
    whos = [b._WHO_BY_SLUG.get(s["slug"]) for s in b.PROGRAMS]
    assert all(whos), "who_its_for uncovered on some rows"
    ratio = len(set(whos)) / len(whos)
    assert ratio >= 0.95, f"who_its_for type-gamed: distinct/total {ratio:.3f} < 0.95"
    # No machine-splice double-period artifact.
    assert not [w for w in whos if ".." in w], "double-period '..' artifact in who_its_for"
