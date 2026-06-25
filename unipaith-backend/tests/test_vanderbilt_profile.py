"""The Vanderbilt profile conforms to the gold standard for its institution, every one of
its eleven schools/colleges, and its full 107-program catalog.

Pure (no DB): builds each node's persisted snapshot from the ``vanderbilt_profile`` module and
runs ``check_conformance``. A node is accepted only when it is gold OR every remaining required
field is recorded in that node's ``_standard.omitted`` (verified-unavailable) with a real
reason. Also guards the matcher-side invariants: no degree_type tier ships entirely null
tuition (except the funded Ph.D. tier), no graduate tuition equals the undergraduate sticker,
and the anti-stub gate is clean.
"""

# ruff: noqa: E501

from collections import defaultdict

from unipaith.data import vanderbilt_profile as v
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.anti_stub import analyze, machine_artifacts, scrape_debris
from unipaith.profile_standard.manifest import MANIFEST


def _institution_snapshot() -> dict:
    so = {**v.SCHOOL_OUTCOMES}
    for path in v._OMITTED_INSTITUTION:
        if path.startswith("school_outcomes."):
            rest = path.split(".", 1)[1]
            if "." not in rest:
                so.pop(rest, None)
            else:
                head, leaf = rest.split(".", 1)
                if isinstance(so.get(head), dict):
                    so[head].pop(leaf, None)
    so["_standard"] = v._standard(v._OMITTED_INSTITUTION)
    return {
        "description_text": v.DESCRIPTION,
        "student_body_size": v.UNDERGRAD_COUNT,
        "media_gallery": [v.SCHOOL_OUTCOMES["campus_photos"][0]["url"]],
        "ranking_data": v.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": v._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = v._ABOUT_DETAIL.get(name)
    if about is not None:
        about = dict(about)
        about["_standard"] = v._standard(v._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in v.SCHOOLS if s["name"] == name),
        "website_url": v._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": v._school_content(name),
    }


def _program_cost(spec: dict) -> dict:
    slug = spec["slug"]
    if slug in v._COST_BY_SLUG:
        return v._COST_BY_SLUG[slug]
    if spec["degree_type"] == "bachelors":
        return {
            "tuition_usd": v._TUITION_UG,
            "total_cost_of_attendance": v._UNDERGRAD_COA,
            "source": v._UG_SRC[0],
            "source_url": v._UG_SRC[1],
        }
    return {"funded": spec["degree_type"] == "phd", "note": "see school page", "source": v._GRAD_PROF_SRC[0], "source_url": v._GRAD_PROF_SRC[1]}


def _program_snapshot(spec: dict) -> dict:
    slug = spec["slug"]
    outcomes = dict(v._OUTCOMES_INSTITUTION)
    outcomes["_standard"] = v._program_standard(slug, spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec["duration_months"],
        "delivery_format": spec["delivery_format"],
        "description_text": spec["description"],
        "website_url": v._SCHOOL_WEBSITE.get(spec["school"]),
        "tracks": v._TRACKS_BY_SLUG.get(slug),
        "application_requirements": v._requirements_for(spec),
        "cost_data": _program_cost(spec),
        "outcomes_data": outcomes,
        "class_profile": v._CLASS_PROFILE_BY_SLUG.get(slug),
        "faculty_contacts": v._FACULTY_BY_SLUG.get(slug),
        "external_reviews": v._REVIEWS_BY_SLUG.get(slug),
        "content_sources": v._program_content(spec["school"], spec["keywords"]),
    }


def _section_gaps_unexpected(level: str, missing_sections: list[str], omitted: set[str]) -> list:
    bad = []
    for secid in missing_sections:
        sec = next(s for s in MANIFEST[level] if s.id == secid)
        req = {f.path for f in sec.fields if f.enrich and f.required}
        if not req <= omitted:
            bad.append(secid)
    return bad


def test_institution_is_gold():
    res = check_conformance("institution", _institution_snapshot(), profile_version=STANDARD_VERSION)
    omitted = set(v._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, f"Unexpected institution gaps: {res.missing_fields}"
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)


def test_all_eleven_schools_done():
    assert len(v.SCHOOLS) == 11
    assert {s["name"] for s in v.SCHOOLS} == set(v._SCHOOL_WEBSITE)
    for school in v.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(v._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, f"{name}: unexpected gaps {res.missing_fields}"
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name


def test_every_program_is_done():
    assert len(v.PROGRAMS) == 107
    for spec in v.PROGRAMS:
        res = check_conformance("program", _program_snapshot(spec), profile_version=STANDARD_VERSION)
        omitted = set(v._program_standard(spec["slug"], spec)["omitted"])
        assert set(res.missing_fields) <= omitted, f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), spec["slug"]


def test_anti_stub_clean():
    progs = v.PROGRAMS
    assert analyze(progs).is_clean, analyze(progs).summary()
    assert machine_artifacts(progs) == []
    assert scrape_debris(progs) == []


def test_no_tuition_tier_is_entirely_null():
    """Matcher-starvation guard: every non-Ph.D. degree_type tier carries at least some
    verified tuition, and no graduate tuition equals the undergraduate sticker (copy-down)."""
    filled = defaultdict(int)
    total = defaultdict(int)
    for spec in v.PROGRAMS:
        dt = spec["degree_type"]
        total[dt] += 1
        if dt == "bachelors" or v._grad_has_verified_tuition(spec):
            filled[dt] += 1
    for dt in total:
        if dt == "phd":
            continue  # research doctorates are funded (omit-with-reason)
        assert filled[dt] > 0, f"tier {dt} ships entirely null tuition"
    grad_rates = {v._COST_BY_SLUG[s]["tuition_usd"] for s in v._COST_BY_SLUG}
    assert v._TUITION_UG not in grad_rates, "graduate tuition must not copy the undergraduate sticker"


def test_reviews_are_gathered_for_flagship_programs():
    """Flagship professional programs carry gathered, cited external_reviews (MBAn shape)."""
    flagships = {
        "vanderbilt-mba", "vanderbilt-ms-finance", "vanderbilt-master-of-accountancy",
        "vanderbilt-juris-doctor", "vanderbilt-doctor-of-medicine",
        "vanderbilt-doctor-nursing-practice", "vanderbilt-med-human-development-counseling",
    }
    assert flagships <= set(v._REVIEWS_BY_SLUG)
    for slug, rev in v._REVIEWS_BY_SLUG.items():
        assert rev["summary"] and rev["themes"] and rev["sources"] and rev["disclaimer"], slug
        assert any(t["sentiment"] in ("caution", "mixed") for t in rev["themes"]), f"{slug} reviews need a real caution"
