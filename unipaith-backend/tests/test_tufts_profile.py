"""Tufts University profile — structural realness invariants (pure, no DB).

Guards the tuftsprof1 catalog (REPAIR_BACKLOG entry #6 seed → gold) against the miss-#2
fabrication classes and the matcher-core coverage gates: every program is a real, distinctly
named conferred degree with a real department, a cip_code, a program-distinct who_its_for,
and a field-specific description; tuition is filled per verified tier or honestly omitted.
The description-quality gates live in test_anti_stub_gate.py (tufts is in CERTIFIED_CLEAN).
"""

# ruff: noqa: E501

from __future__ import annotations

import re

from unipaith.data import tufts_profile as t

P = t.PROGRAMS


def test_catalog_size_and_schools():
    assert len(P) == 136
    school_names = {s["name"] for s in t.SCHOOLS}
    assert len(t.SCHOOLS) == 8
    assert {p["school"] for p in P} == school_names  # every program maps to a real school


def test_no_duplicate_rendered_names_or_slugs():
    names = [(p["program_name"], p["degree_type"]) for p in P]
    assert len(names) == len(set(names)), "duplicate (program_name, degree_type)"
    slugs = [p["slug"] for p in P]
    assert len(slugs) == len(set(slugs)), "duplicate slug"


def test_no_stub_or_rollup_or_placeholder_names():
    bare = {"ba", "bs", "ma", "ms", "phd", "mfa", "science", "engineering"}
    rollup = re.compile(r",\s*(general|other)$|\(cip\s*\d|and related|literatures, and", re.I)
    placeholder = re.compile(r"^(professional|graduate|doctoral|undergraduate)\s+(program|degree)\s+in\b", re.I)
    possessive = re.compile(r"^(bachelor|master|doctorate)'s\s+in\b", re.I)
    for p in P:
        name = p["program_name"]
        field = name.split(" in ", 1)[-1]
        assert name.strip().lower() not in bare, f"bare-abbreviation name: {name}"
        assert not rollup.search(name), f"CIP-rollup name: {name}"
        assert not rollup.search(p["department"]), f"CIP-rollup department: {p['department']}"
        assert not placeholder.match(name), f"degree-type placeholder name: {name}"
        assert not possessive.match(name), f"possessive-mint name: {name}"
        # field part title-cased (no mid-name lowercase content word)
        for w in re.sub(r"\([^)]*\)", "", field).split()[1:]:
            wl = w.strip(",.:'")
            if wl and wl[0].islower() and wl.lower() not in {
                "and", "of", "the", "in", "for", "to", "a", "an", "or", "on", "with", "at", "by", "as",
            } and not any(c in w for c in "./'"):
                raise AssertionError(f"sentence-cased field word in: {name}")


def test_real_departments():
    for p in P:
        dept = p["department"]
        assert dept and dept.strip(), f"null/blank department: {p['slug']}"
        assert dept != "Programs", f"placeholder department: {p['slug']}"
        assert not re.fullmatch(r"[A-Z]{2,4}", dept), f"credential-abbreviation department: {dept}"


def test_matcher_core_cip_and_who_and_description_coverage():
    assert all(p.get("cip") for p in P), "cip_code must be 100% covered"
    whos = [p["who"] for p in P]
    descs = [p["description"] for p in P]
    # program-distinct (never a degree-type template): distinct ≈ total
    assert len(set(whos)) == len(whos), "who_its_for must be program-distinct"
    assert len(set(descs)) == len(descs), "description_text must be program-distinct"
    # descriptions terminate (no scraped-debris truncation) and are field-specific length
    for p in P:
        d = p["description"].strip()
        assert d.endswith((".", "!", "?")), f"non-terminated description: {p['slug']}"
        assert len(d) > 40, f"too-short description: {p['slug']}"


def test_tuition_tiers_verified_or_omitted():
    from collections import defaultdict

    tier = defaultdict(lambda: [0, 0])
    for p in P:
        tier[p["degree_type"]][1] += 1
        if t._resolve_tuition(p) is not None:
            tier[p["degree_type"]][0] += 1
    # Undergraduate sticker on every bachelor's; funded PhDs (0) on every doctoral row.
    assert tier["bachelors"][0] == tier["bachelors"][1], "every bachelor's carries the UG sticker"
    assert tier["phd"][0] == tier["phd"][1], "every PhD carries the funded (0) scalar"
    # Master's tier majority-filled (AS&E per-credit + Fletcher flat); the residual are
    # school-specific rates honestly omitted-with-reason — never a whole-tier null.
    filled, total = tier["masters"]
    assert filled >= total * 0.6, f"master's tuition coverage too low: {filled}/{total}"
    # No graduate/professional row copies the undergraduate sticker.
    ug = t._TUITION_UG
    for p in P:
        if p["degree_type"] in ("masters", "phd", "professional"):
            assert t._resolve_tuition(p) != ug, f"grad/prof row carries UG sticker: {p['slug']}"


def test_every_program_has_content_source_feed():
    for p in P:
        cs = t._program_content(p)
        assert cs.get("news_rss") and cs.get("events_feed"), f"dead feed: {p['slug']}"
