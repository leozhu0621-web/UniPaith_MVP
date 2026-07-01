"""The UT Austin profile conforms to the gold standard across its WHOLE tree — the
institution, every one of its 18 real schools/academic units, and every one of
its 338 programs — mirroring the MIT/Sloan/MBAn reference certification.

Pure (no DB): builds each node's persisted snapshot from the ``ut_austin_profile``
module exactly as ``apply()`` writes it, and runs ``check_conformance``. A node
passes when it is gold OR every remaining required gap is recorded in that node's
``_standard.omitted``.
"""

from pathlib import Path

from unipaith.data import ut_austin_profile as u
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
    # cost_data mirrors what apply() writes (per-credential published tuition; AuD bills at
    # the standard graduate rate, DNP carries its published program total, and only the
    # Pharm.D. annual scalar is omitted — its rate is published solely in a non-machine-
    # readable Box PDF).
    _tuition, cost = u._program_tuition(spec)
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
        "who_its_for": u._WHO_BY_SLUG.get(slug),
    }


# Connectives that may stay lowercase mid-name; everything else must be title-cased
# (REPAIR_BACKLOG #4b name-casing gate).
_NAME_CONNECTIVES = {
    "and", "of", "the", "in", "for", "to", "a", "an", "or", "on",
    "with", "at", "by", "as", "vs",
}


def _sentence_cased_words(name: str) -> list[str]:
    """Mid-name content words shipped lowercase (sentence-casing defect), with the run-94
    carve-outs: a leading word, a connective, a parenthetical qualifier, and a token with an
    interior capital (acronym / slash form / possessive) are all legitimate."""
    bad: list[str] = []
    for i, w in enumerate(name.split(" ")):
        if not w or i == 0 or w.startswith("("):
            continue
        if any(c.isupper() for c in w[1:]):  # acronym / mixed-case / slash form
            continue
        if w.lower() in _NAME_CONNECTIVES:
            continue
        first = next((c for c in w if c.isalpha()), "")
        if first and first.islower():
            bad.append(w)
    return bad


def test_catalog_breadth_and_shape():
    # Full published degree catalog across UT Austin's 18 colleges/schools.
    assert len(u.SCHOOLS) == 18
    assert len(u.PROGRAMS) >= 300
    assert len(set(u.PROGRAM_SLUGS)) == len(u.PROGRAM_SLUGS)
    from unipaith.data.profile_catalog_utils import validate_catalog

    assert not validate_catalog(u.PROGRAMS)
    # online delivery is set on the Computer & Data Science Online programs
    assert any(p["delivery_format"] == "online" for p in u.PROGRAMS)
    # ownership + classification drive the explore-card eyebrow
    assert u.RANKING_DATA["ownership_type"] == "public"
    assert "public research university" in u.DESCRIPTION.lower()
    assert u._INSTITUTION_CONTENT.get("news_rss") == "https://news.utexas.edu/feed/"


def test_institution_is_gold_except_recorded_omission():
    snap = _institution_snapshot()
    res = check_conformance("institution", snap, profile_version=STANDARD_VERSION)
    bad = _gaps("institution", res, set(u._OMITTED_INSTITUTION))
    assert not bad, f"Unexpected institution gaps: {bad}"
    assert "school_outcomes.employed_or_continuing_ed" in u._OMITTED_INSTITUTION


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
    # Beat the "1 reviewed program" bug: coverable flagships carry external_reviews.
    for slug in (
        "ut-austin-business-administration-mba",
        "ut-austin-law-jd",
        "ut-austin-medicine-md",
        "ut-austin-computer-science-bsa",
        "ut-austin-computer-science-online-ms",
        "ut-austin-business-administration-bba",
        "ut-austin-accounting-mpa",
        "ut-austin-business-analytics-ms",
        "ut-austin-petroleum-engineering-bspe",
        "ut-austin-electrical-and-computer-engineering-bsece",
        "ut-austin-mechanical-engineering-bsme",
        "ut-austin-public-affairs-mpaff",
        "ut-austin-nursing-bsn",
    ):
        assert slug in u._REVIEWS_BY_SLUG, f"{slug} should carry external_reviews"
        rev = u._REVIEWS_BY_SLUG[slug]
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"]
    # MBA + JD also carry verified employment outcomes.
    for slug in ("ut-austin-business-administration-mba", "ut-austin-law-jd"):
        o = u._OUTCOMES_BY_SLUG[slug]
        assert o["employment_rate"] and o["conditions"] and o["source"]


def test_who_its_for_is_complete_and_program_distinct():
    """`who_its_for` is a UNIVERSAL depth field: filled on EVERY program (no 0% / hard-null,
    REPAIR_BACKLOG #3a) AND program-DISTINCT, never a degree-type template (#3b). Gold-bar:
    distinct/total approaches 1.0; the type-gaming FAIL threshold is well under ~0.5."""
    vals = [u._WHO_BY_SLUG.get(s) for s in u.PROGRAM_SLUGS]
    assert all(isinstance(v, str) and v.strip() for v in vals), (
        "who_its_for must be filled on every program"
    )
    # No program hard-nulls the field in apply() (a literal `p.who_its_for = None` code line).
    module = Path(__file__).resolve().parents[1] / "src/unipaith/data/ut_austin_profile.py"
    code_lines = {
        ln.strip() for ln in module.read_text().splitlines() if not ln.lstrip().startswith("#")
    }
    assert "p.who_its_for = None" not in code_lines, (
        "who_its_for must not be hard-nulled in apply()"
    )
    distinct_ratio = len(set(vals)) / len(vals)
    assert distinct_ratio >= 0.9, (
        f"who_its_for type-gamed: distinct/total={distinct_ratio:.2f} (gold ~1.0)"
    )


def test_program_names_are_title_cased():
    """Every program_name (and department) carries UT Austin's published title case — no
    mid-name lowercase content word (REPAIR_BACKLOG #4b sentence-casing defect)."""
    offenders = []
    for p in u.PROGRAMS:
        for field in (p["program_name"], p.get("department") or ""):
            bad = _sentence_cased_words(field)
            if bad:
                offenders.append((field, bad))
    assert not offenders, f"sentence-cased names: {offenders[:5]}"


def test_professional_and_masters_tuition_filled_or_omitted_with_reason():
    """The matcher-core master's/professional tuition tier is filled with a published rate
    or recorded in `_standard.omitted` — never a silent null (REPAIR_BACKLOG #1)."""
    for spec in u.PROGRAMS:
        if spec["degree_type"] not in ("masters", "professional"):
            continue
        scalar, _cost = u._program_tuition(spec)
        if scalar is None:
            omitted = u._program_standard(spec["slug"], spec)["omitted"]
            assert "cost_data.tuition_usd" in omitted, (
                f"{spec['slug']} has null tuition not recorded in _standard.omitted"
            )
    # AuD (standard graduate rate) and the academic MS in Accounting (standard graduate rate)
    # carry a published annual scalar.
    for slug in ("ut-austin-audiology-aud", "ut-austin-accounting-ms"):
        spec = next(s for s in u.PROGRAMS if s["slug"] == slug)
        scalar, _cost = u._program_tuition(spec)
        assert scalar and scalar > 0, f"{slug} should carry a published tuition scalar"
    # The DNP bills a published FLAT per-semester rate ($6,000, residency-independent), so it
    # carries a real ANNUAL scalar ($12,000/yr = $6,000 × the standard Fall+Spring year) and is
    # NOT omitted (REPAIR_BACKLOG #1 — professional tier filled). The full $30,000 program total
    # is preserved in cost_data. program.tuition is consumed as ANNUAL by the matcher, so the
    # scalar must be the annual figure, never the multi-year total (PR #1236 review).
    dnp = next(s for s in u.PROGRAMS if s["slug"] == "ut-austin-nursing-dnp")
    dnp_scalar, dnp_cost = u._program_tuition(dnp)
    assert dnp_scalar == 12000, "DNP matcher scalar must be the flat annual rate, not the total"
    assert dnp_cost.get("tuition_usd") == 12000, "DNP cost card shows the annual rate"
    assert dnp_cost.get("total_program_tuition") == 30000, "DNP keeps the full program total"
    assert "tuition_period" not in dnp_cost, "DNP scalar is annual, not a program-total period"
    assert "cost_data.tuition_usd" not in u._program_standard(dnp["slug"], dnp)["omitted"], (
        "DNP annual rate is filled, not omitted"
    )
    # The online CS/DS/AI master's publish a single FLAT $10,000 total ($333/credit × 30, the
    # same for residents, non-residents, and international students), completed flexibly part-time,
    # so the flat program total IS the de-facto cost basis and carries the matcher budget scalar
    # (the lowest-cost graduate option in the catalog) — never a silent null (REPAIR_BACKLOG #1).
    for slug in (
        "ut-austin-computer-science-online-ms",
        "ut-austin-data-science-ms",
        "ut-austin-artificial-intelligence-ms",
    ):
        spec = next(s for s in u.PROGRAMS if s["slug"] == slug)
        scalar, cost = u._program_tuition(spec)
        assert scalar == 10000, f"{slug} carries the verified flat $10,000 program total"
        assert cost.get("tuition_usd") == 10000, f"{slug} cost card shows the flat total"
        assert cost.get("total_program_tuition") == 10000, f"{slug} keeps the published total"
        assert cost["breakdown"]["tuition_out_of_state"] == 10000, f"{slug} is residency-flat"
        assert "cost_data.tuition_usd" not in u._program_standard(slug, spec)["omitted"], (
            f"{slug} tuition is filled, not omitted"
        )
    # The academic MS in Information, Risk & Operations Management and MS in Management are
    # research master's offered only within their McCombs doctoral program (like the MS in
    # Accounting), so both bill at UT's STANDARD graduate rate and carry that scalar — not omitted.
    for slug in (
        "ut-austin-information-risk-and-operations-management-ms",
        "ut-austin-management-ms",
    ):
        spec = next(s for s in u.PROGRAMS if s["slug"] == slug)
        scalar, _cost = u._program_tuition(spec)
        assert scalar == u._TUITION_GRAD_OOS, (
            f"{slug} bills the standard graduate non-resident rate"
        )
        assert "cost_data.tuition_usd" not in u._program_standard(slug, spec)["omitted"], (
            f"{slug} tuition is filled, not omitted"
        )
    # Only the Pharm.D. (calculator/PDF-only, unverifiable to two sources) and MS Energy
    # Management (premium professional cohort, no published rate) remain honestly omitted.
    for slug in ("ut-austin-pharmacy-pharmd", "ut-austin-energy-management-ms"):
        spec = next(s for s in u.PROGRAMS if s["slug"] == slug)
        scalar, _cost = u._program_tuition(spec)
        assert scalar is None, f"{slug} scalar is honestly omitted"
        assert "cost_data.tuition_usd" in u._program_standard(slug, spec)["omitted"], (
            f"{slug} null tuition must be recorded in _standard.omitted"
        )
