"""The UCLA profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 13 real schools/colleges, and every one of its 372
programs — mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``ucla_profile`` module
exactly as ``apply()`` writes it, and runs ``check_conformance``. A node passes when it
is gold OR every remaining required gap is recorded in that node's ``_standard.omitted``.
"""

from unipaith.data import ucla_profile as u
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
    cost = u._cost_for(spec)[1]
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
        "tracks": None,
        "application_requirements": u._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": u._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": u._FACULTY_BY_SLUG.get(slug),
        "external_reviews": u._REVIEWS_BY_SLUG.get(slug),
        "content_sources": u._program_content(spec["school"], kw),
    }


def test_catalog_breadth_and_shape():
    # Full published degree catalog across the College + 12 professional schools.
    assert len(u.SCHOOLS) == 13
    assert len(u.PROGRAMS) >= 370
    assert len(set(u.PROGRAM_SLUGS)) == len(u.PROGRAM_SLUGS)
    # online delivery is set on the Samueli MSOL tracks
    assert any(p["delivery_format"] == "online" for p in u.PROGRAMS)
    # ownership + classification drive the explore-card eyebrow
    assert u.RANKING_DATA["ownership_type"] == "public"
    assert "private" not in u.DESCRIPTION.split(".")[0].lower()
    assert "public research university" in u.DESCRIPTION.lower()
    # De-fabrication: no school-blurb stubs; real owning school in department
    assert not any("connects to" in (p.get("description") or "") for p in u.PROGRAMS)
    assert not any("Students build depth" in (p.get("description") or "") for p in u.PROGRAMS)
    assert all(p.get("department") == p["school"] for p in u.PROGRAMS)


def test_ucla_catalog_has_no_frame_stripped_shared_body():
    from unipaith.profile_standard.anti_stub import analyze, frame_stripped_shared_body

    report = analyze(u.PROGRAMS)
    assert report.is_clean, f"UCLA anti-stub regressed: {report.summary()}"
    shared = frame_stripped_shared_body(u.PROGRAMS, abs_chars=150)
    assert not shared, (
        f"UCLA credential siblings share a frame-stripped body on "
        f"{len(shared)} field(s): {shared[:8]}{' …' if len(shared) > 8 else ''}"
    )


def test_catalog_descriptions_are_field_specific_and_real():
    from unipaith.profile_standard.anti_stub import analyze

    report = analyze(u.PROGRAMS)
    assert report.is_clean, f"UCLA catalog is not anti-stub clean: {report.summary()}"


def test_no_template_slot_machine_broken_grammar():
    """REPAIR_BACKLOG CRITICAL C2: per-credential slot frames must not ship broken grammar.

    The run-71 defect slotted a raw fragment into a sentence frame ("research in of
    artistic production…", "…understanding of human."). Gold MIT scores 0.
    """
    hits = u._template_slot_artifacts(u.PROGRAMS)
    assert not hits, f"UCLA has {len(hits)} template-slot grammar rows: {hits[:5]}"


def test_machine_artifacts_clean():
    from unipaith.profile_standard.anti_stub import machine_artifacts, scrape_debris

    assert not machine_artifacts(u.PROGRAMS)
    assert not scrape_debris(u.PROGRAMS)


def test_matcher_core_tuition_is_published_catalog_wide():
    """REPAIR_BACKLOG #3 + #7: tuition is institution-published, so it is filled for every
    knowable credential level — the undergrad sticker, the academic graduate rate, funded
    research-doctoral $0, AND the school-billed professional / self-supporting master's at their
    OWN published rates (not the undergrad sticker, never the academic rate copied down, never
    guessed). Only a degree with no fetchable published figure omits-with-reason."""
    assert u._TUITION_UG_IN_STATE > 0
    assert u._TUITION_GRAD > 0
    have = [p for p in u.PROGRAMS if u._cost_for(p)[0] is not None]
    # Bachelor's + academic + professional/self-supporting master's + funded PhD now cover
    # essentially the whole catalog; only the M.F.A. (PDST-inclusive total unpublished) and a
    # few professional doctorates (Ed.D., S.J.D., D.Env., D.M.A.) omit-with-reason.
    assert len(have) / len(u.PROGRAMS) >= 0.97
    # Every master's now carries a published tuition except the M.F.A. (no fetchable PDST total).
    null_masters = [
        p["slug"]
        for p in u.PROGRAMS
        if p["degree_type"] == "masters" and u._cost_for(p)[0] is None
    ]
    assert null_masters == ["ucla-film-and-television-mfa-ms"], null_masters
    # A self-supporting online master's (MSOL) carries its REAL published rate, not the academic
    # rate copied across — and not the undergrad sticker.
    msol = next(p for p in u.PROGRAMS if p["slug"] == "ucla-engineering-ms")
    mtui, mcost = u._cost_for(msol)
    assert mtui == 19_800 and "msol.ucla.edu" in mcost["source_url"]
    assert mtui not in (u._TUITION_GRAD, u._TUITION_UG_IN_STATE)
    # A professional master's (MBA) carries the school's own published program fee, sourced.
    mba = next(p for p in u.PROGRAMS if p["slug"] == "ucla-master-of-business-administration-ms")
    btui, bcost = u._cost_for(mba)
    assert btui == 82_733 and "anderson.ucla.edu" in bcost["source_url"]
    assert "cost_data.tuition_usd" not in u._program_standard(mba["slug"], mba)["omitted"]
    # The M.F.A. is the lone omit-with-reason master's (PDST-inclusive annual total not published).
    mfa = next(p for p in u.PROGRAMS if p["slug"] == "ucla-film-and-television-mfa-ms")
    assert u._cost_for(mfa)[0] is None
    assert "cost_data.tuition_usd" in u._program_standard(mfa["slug"], mfa)["omitted"]
    # A professional doctorate (Ed.D.) is omitted, never zeroed as funded.
    edd = next(p for p in u.PROGRAMS if p["slug"] == "ucla-doctor-of-education-phd")
    assert u._cost_for(edd)[0] is None
    # A research Doctor of Philosophy is funded $0 (present budget-fit signal).
    research_phd = next(
        p for p in u.PROGRAMS if p["program_name"].startswith("Doctor of Philosophy")
    )
    assert u._cost_for(research_phd) == (0, u._phd_funded_cost())
    # The fabricated "Master of Science in Management" (no such Anderson degree — Anderson awards
    # only the MFE and MSBA as standalone master's) is dropped; the real Ph.D. in Management stays.
    assert not any(p["slug"] == "ucla-management-ms" for p in u.PROGRAMS)
    assert not any(p["program_name"] == "Master of Science in Management" for p in u.PROGRAMS)
    assert any(p["slug"] == "ucla-management-phd" for p in u.PROGRAMS)


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


def test_flagship_programs_carry_reviews_and_outcomes():
    # Beat the "1 reviewed program" bug: the coverable flagships carry external_reviews.
    for slug in (
        "ucla-master-of-business-administration-ms",
        "ucla-juris-doctor-prof",
        "ucla-doctor-of-medicine-prof",
        "ucla-computer-science-ug",
        "ucla-master-of-financial-engineering-ms",
        "ucla-business-economics-ug",
        "ucla-film-and-television-ug",
    ):
        assert slug in u._REVIEWS_BY_SLUG, f"{slug} should carry external_reviews"
        rev = u._REVIEWS_BY_SLUG[slug]
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]
    # MBA + JD also carry verified employment outcomes.
    for slug in ("ucla-master-of-business-administration-ms", "ucla-juris-doctor-prof"):
        o = u._OUTCOMES_BY_SLUG[slug]
        assert o["median_salary"] and o["employment_rate"] and o["conditions"] and o["source"]
