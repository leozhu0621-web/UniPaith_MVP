"""Lehigh University conforms to the gold standard across its WHOLE tree — the
institution, all five colleges, and every one of its 164 programs — mirroring the
MIT / Boston College reference instances.

Lehigh entered as a bare U.S. News seed (0 programs). This build takes it to gold:
the institution report card, a real 164-program catalog with field-specific
descriptions and program-distinct ``who_its_for`` across the five colleges, the
per-college graduate tuition tiers (every master's carries a distinct computed
published rate, never the undergraduate sticker copied down), and ``cip_code`` on
every row. The assertions below lock those invariants so a later re-apply cannot
silently regress them, and — per SKILL.md §8.5 — assert the anti-stub gates
programmatically (gold-MIT-0%) so a stub-swap PR cannot pass CI.
"""


from unipaith.data import lehigh_profile as p
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.anti_stub import analyze
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


# ── Snapshot builders — mirror _apply_* so the pure test matches persisted rows ──
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


def _school_snapshot(spec: dict) -> dict:
    about = {
        **p._ABOUT_DETAIL.get(spec["name"], {}),
        "source": {"label": "Lehigh University - Academics", "url": "https://www2.lehigh.edu/academics"},
        "_standard": p._standard(p._ABOUT_OMITTED[spec["name"]]),
    }
    return {
        "name": spec["name"],
        "description_text": spec["description"],
        "website_url": p._SCHOOL_WEBSITE.get(spec["name"]),
        "about_detail": about,
        "content_sources": p._school_content(spec["name"]),
    }


def _program_snapshot(spec: dict) -> tuple[dict, set[str]]:
    _tuition, cost = p._program_cost(spec)
    std = p._program_standard(spec)
    outcomes = {**p._OUTCOMES_INSTITUTION, "_standard": std}
    snap = {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": p._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": spec.get("tracks"),
        "application_requirements": p._requirements_for(spec),
        "cost_data": cost,
        "outcomes_data": outcomes,
        "class_profile": None,
        "faculty_contacts": None,
        "external_reviews": None,
        "content_sources": p._program_content(spec["school"], p._program_keywords(spec)),
        "who_its_for": p._who_its_for(spec),
    }
    return snap, set(std["omitted"])


def test_institution_is_gold():
    res = check_conformance(
        "institution", _institution_snapshot(), profile_version=STANDARD_VERSION
    )
    assert _gaps("institution", res, set(p._OMITTED_INSTITUTION)) == set()


def test_every_school_is_gold():
    assert len(p.SCHOOLS) == 5
    for spec in p.SCHOOLS:
        res = check_conformance("school", _school_snapshot(spec), profile_version=STANDARD_VERSION)
        assert _gaps("school", res, set(p._ABOUT_OMITTED[spec["name"]])) == set(), spec["name"]


def test_every_program_is_gold():
    assert len(p.PROGRAMS) == 164
    for spec in p.PROGRAMS:
        snap, omitted = _program_snapshot(spec)
        res = check_conformance("program", snap, profile_version=STANDARD_VERSION)
        assert _gaps("program", res, omitted) == set(), spec["slug"]


def test_no_duplicate_or_stub_names():
    keys = [(s["program_name"], s["degree_type"]) for s in p.PROGRAMS]
    assert len(set(keys)) == len(keys)  # no duplicate rendered (name, degree)
    for s in p.PROGRAMS:
        name = s["program_name"]
        assert name.strip() not in {"BA", "BS", "MS", "MA", "PhD", "MBA"}  # no bare abbreviations
        assert s["department"] and s["department"] != "Programs"
        assert ", General" not in name and ", Other" not in name  # no CIP-rollup tell
        assert "(CIP " not in name and "(CIP " not in s["department"]  # no literal CIP code


def test_master_and_paid_doctorate_tuition_is_annual_and_distinct():
    """Every master's AND the paid Ed.D. carries an ANNUAL graduate rate distinct from the
    undergraduate sticker (per-credit x the 18-credit registrar full-time year); funded
    research doctorates omit the figure with funded=True."""
    for s in p.PROGRAMS:
        if p._is_paid_grad(s):
            tuition, cost = p._program_cost(s)
            assert tuition is not None and tuition != p._UG_TUITION, s["slug"]
            rate = p._GRAD_RATE_OVERRIDE.get(s["slug"], p._GRAD_RATE[s["school"]])
            credits = p._ANNUAL_CREDITS_OVERRIDE.get(s["slug"], p._GRAD_ANNUAL_CREDITS)
            assert tuition == rate * credits, s["slug"]
            assert cost.get("funded") is False, s["slug"]
        elif s["degree_type"] == "phd":
            tuition, cost = p._program_cost(s)
            assert tuition is None and cost.get("funded") is True, s["slug"]


def test_graduate_full_time_load_matches_registrar():
    # Lehigh's registrar full-time graduate load is 9 credits/semester = 18/year.
    assert p._GRAD_ANNUAL_CREDITS == 18


def test_accelerated_programs_priced_at_full_year_load():
    """Programs that finish inside one academic year (<=12 months) charge their FULL degree
    credits that year, so their annual tuition is the whole program - not the 18-credit minimum."""
    for slug in p._ANNUAL_CREDITS_OVERRIDE:
        s = next(x for x in p.PROGRAMS if x["slug"] == slug)
        assert s["duration_months"] <= 12, slug
        tuition, _ = p._program_cost(s)
        rate = p._GRAD_RATE_OVERRIDE.get(slug, p._GRAD_RATE[s["school"]])
        assert tuition == rate * p._ANNUAL_CREDITS_OVERRIDE[slug] > rate * p._GRAD_ANNUAL_CREDITS


def test_edd_duration_is_not_research_phd_default():
    edd = next(s for s in p.PROGRAMS if s["slug"] == "lehigh-educational-leadership-edd")
    assert edd["duration_months"] == 48  # not the 60-month research-PhD default


def test_part_time_flag_for_flexible_programs():
    # The part-time professional Ed.D. and online/hybrid programs are part-time-available so a
    # wants_part_time searcher is not penalized against them.
    edd = next(s for s in p.PROGRAMS if s["slug"] == "lehigh-educational-leadership-edd")
    assert edd["slug"] in p._PART_TIME_SLUGS
    assert any(s["delivery_format"] in ("online", "hybrid") for s in p.PROGRAMS)


def test_full_time_mba_uses_published_credit_load():
    # Lehigh's one-year Full-Time MBA is a 42-credit curriculum (27 core + 15 electives).
    assert p._ANNUAL_CREDITS_OVERRIDE["lehigh-mba-fulltime"] == 42


def test_edd_is_paid_doctorate_in_doctoral_family():
    """The Ed.D. stays degree_type 'phd' (so the matcher's doctoral degree-level fit matches an
    Ed.D. search) but is a PAID professional doctorate (tuition filled, not funded) with
    non-research fit messaging."""
    edd = next(s for s in p.PROGRAMS if s["slug"] == "lehigh-educational-leadership-edd")
    assert edd["degree_type"] == "phd"
    assert p._is_paid_grad(edd)
    tuition, cost = p._program_cost(edd)
    assert tuition is not None and cost.get("funded") is False
    who = p._who_its_for(edd)
    assert "original research" not in who and "national-lab" not in who


def test_one_year_mba_duration():
    mba = next(s for s in p.PROGRAMS if s["slug"] == "lehigh-mba-fulltime")
    assert mba["duration_months"] == 12


def test_ranking_data_overwrites_stale_seed_facts():
    # The bulk seed shipped acceptance_rate 0.3698 / graduation_rate 1.0; the enrichment must
    # overwrite those keys (institution cards + match fallback read them directly).
    assert p.RANKING_DATA["acceptance_rate"] == 0.2593
    assert p.RANKING_DATA["graduation_rate"] == 0.8791


def test_cip_on_every_program():
    import re
    for s in p.PROGRAMS:
        assert re.fullmatch(r"\d{2}\.\d{2,4}", s["cip"]), s["slug"]


def test_who_its_for_is_program_distinct():
    who = [p._who_its_for(s) for s in p.PROGRAMS]
    assert len(set(who)) == len(who)


def test_anti_stub_gates_are_gold_mit_zero():
    """SKILL.md §8.5: descriptions pass the anti-stub gates baselined to gold MIT 0%."""
    descs = [
        {
            "program_name": s["program_name"],
            "degree_type": s["degree_type"],
            "department": s["department"],
            "description_text": s["description"],
            "school": s["school"],
        }
        for s in p.PROGRAMS
    ]
    result = analyze(descs)
    assert result.is_clean, result

    # No description is shared verbatim across programs (per-field/school stamping tell).
    bodies = [s["description"] for s in p.PROGRAMS]
    assert len(set(bodies)) == len(bodies)
    # No description restates its own program_name (page-heading doubling tell).
    for s in p.PROGRAMS:
        assert not s["description"].startswith(s["program_name"]), s["slug"]
