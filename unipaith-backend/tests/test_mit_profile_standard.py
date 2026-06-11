"""The MIT profile conforms to the gold standard for its institution, every one of its
six schools, and its full program catalog.

Pure (no DB): builds each node's persisted snapshot from the ``mit_profile`` module and
runs ``check_conformance``. A node is accepted only when it is gold OR every remaining
required field is recorded in that node's ``_standard.omitted`` (verified-unavailable)
with a real reason. This is the regression guard that MIT — the gold reference instance —
stays at the current ``STANDARD_VERSION`` with feeds + ``_standard`` stamps on every node.
"""

# ruff: noqa: E501

from unipaith.data import mit_profile as m
from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST


def _institution_snapshot() -> dict:
    so = {**m.SCHOOL_OUTCOMES}
    so["_standard"] = m._standard(m._OMITTED_INSTITUTION)
    return {
        "description_text": m.DESCRIPTION,
        "student_body_size": m.UNDERGRAD_COUNT,
        "media_gallery": [m._CAMPUS_PHOTO],
        "ranking_data": m.RANKING_DATA,
        "school_outcomes": so,
        "content_sources": m._INSTITUTION_CONTENT,
    }


def _school_snapshot(name: str) -> dict:
    about = dict(m._SCHOOL_ABOUT[name])
    about["_standard"] = m._standard(m._ABOUT_OMITTED.get(name, []))
    return {
        "name": name,
        "description_text": next(s["description"] for s in m.SCHOOLS if s["name"] == name),
        "website_url": m._SCHOOL_WEBSITE.get(name),
        "about_detail": about,
        "content_sources": (
            m._SLOAN_CONTENT if name == m._SLOAN else m._school_content(name)
        ),
    }


def _program_snapshot(spec: dict) -> dict:
    """Mirror what _apply_programs persists, at the granularity conformance checks."""
    slug = spec["slug"]
    kind = m._outcomes_kind(spec)
    outcomes: dict = {}
    if kind == "full":
        outcomes = {
            "median_salary": 1,
            "employment_rate": 1,
            "top_industries": ["x"],
            "conditions": ["x"],
            "source": "x",
        }
    elif kind == "fos":
        outcomes = {"median_salary": 1, "source": "x"}
    elif kind == "institution":
        outcomes = {"median_salary": 1, "employment_rate": 1, "top_industries": ["x"], "source": "x"}
    outcomes["_standard"] = m._program_standard(spec)
    return {
        "program_name": spec["program_name"],
        "degree_type": spec["degree_type"],
        "duration_months": spec.get("duration_months"),
        "delivery_format": spec.get("delivery_format", "in_person"),
        "description_text": spec["description"],
        "website_url": m._WEBSITE_BY_SLUG.get(slug) or m._SCHOOL_WEBSITE.get(spec["school"]),
        "department": "x",
        "who_its_for": "x",
        "highlights": ["x"],
        "tracks": ["x"] if slug in m._TRACKS_BY_SLUG else None,
        "application_requirements": {
            "materials": ["x"],
            "source": "x",
            **({} if m._uses_req_open(spec) else {"deadlines": ["x"]}),
        },
        "cost_data": ({"tuition_usd": 1, "source": "x"} if m._has_tuition(spec) else None),
        "outcomes_data": outcomes,
        "class_profile": ({"cohort_size": "x"} if slug in m._CLASS_PROFILE_BY_SLUG else None),
        "faculty_contacts": ({"lead": ["x"]} if slug in m._FACULTY_BY_SLUG else None),
        "external_reviews": ({"summary": "x"} if slug in m._REVIEWS_BY_SLUG else None),
        "content_sources": (m._MBAN_CONTENT if slug == "mit-sloan-mban" else m._program_content(spec)),
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
    omitted = set(m._OMITTED_INSTITUTION)
    assert set(res.missing_fields) <= omitted, f"Unexpected institution gaps: {res.missing_fields}"
    assert not _section_gaps_unexpected("institution", res.missing_sections, omitted)


def test_all_six_schools_done():
    assert len(m.SCHOOLS) == 6
    assert {s["name"] for s in m.SCHOOLS} == set(m._SCHOOL_ABOUT)
    assert {s["name"] for s in m.SCHOOLS} == set(m._SCHOOL_WEBSITE)
    for school in m.SCHOOLS:
        name = school["name"]
        res = check_conformance("school", _school_snapshot(name), profile_version=STANDARD_VERSION)
        omitted = set(m._ABOUT_OMITTED.get(name, []))
        assert set(res.missing_fields) <= omitted, f"{name}: unexpected gaps {res.missing_fields}"
        assert not _section_gaps_unexpected("school", res.missing_sections, omitted), name


def test_every_program_is_done():
    assert len(m.PROGRAMS) == 65, "the full MIT program catalog (gold reference)"
    for spec in m.PROGRAMS:
        res = check_conformance("program", _program_snapshot(spec), profile_version=STANDARD_VERSION)
        omitted = set(m._program_standard(spec)["omitted"])
        assert set(res.missing_fields) <= omitted, f"{spec['slug']}: gaps {set(res.missing_fields) - omitted}"
        assert not _section_gaps_unexpected("program", res.missing_sections, omitted), spec["slug"]


def test_every_program_maps_to_a_real_school():
    names = {s["name"] for s in m.SCHOOLS}
    for spec in m.PROGRAMS:
        assert spec["school"] in names, f"{spec['slug']} -> unknown school {spec['school']}"
    assert len(m.PROGRAM_SLUGS) == len(set(m.PROGRAM_SLUGS)), "duplicate program slug"


def test_every_program_has_delivery_format():
    fmts = {p.get("delivery_format", "in_person") for p in m.PROGRAMS}
    assert fmts <= {"in_person", "online", "hybrid"}


def test_every_node_has_content_sources():
    assert m._INSTITUTION_CONTENT.get("news_rss")
    for school in m.SCHOOLS:
        name = school["name"]
        cs = m._SLOAN_CONTENT if name == m._SLOAN else m._school_content(name)
        assert cs.get("news_rss") and cs.get("events_feed"), name
    for spec in m.PROGRAMS:
        cs = m._MBAN_CONTENT if spec["slug"] == "mit-sloan-mban" else m._program_content(spec)
        assert cs.get("news_rss") and cs.get("events_feed") and cs.get("keywords"), spec["slug"]
