#!/usr/bin/env python3
"""Accurate fleet audit for enrich-profile repair selection."""
from __future__ import annotations

import importlib
import pkgutil
import re

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

TEMPLATE_RE = re.compile(
    r" — a .+ (bachelors|masters|doctoral|professional|certificate) program offered through "
)

COVERABLE_KEYWORDS = (
    "mba", "mban", "computer science", "data science", "analytics", "finance",
    "engineering", "public health", "mph", "mpp", "jd", "law", "medicine", "md",
    "architecture", "economics", "business", "nursing", "mscs", "mfin", "meng",
    "social work", "journalism", "hospitality", "film", "biomedical", "march",
    "mha", "mfa", "msw", "dmd", "dentistry",
)


def load(name: str):
    return importlib.import_module(f"unipaith.data.{name}_profile")


def get_program_cs(mod, spec: dict):
    if hasattr(mod, "_program_content_for"):
        return mod._program_content_for(spec)
    slug = spec.get("slug", "")
    school = spec.get("school", "")
    kw_map = getattr(mod, "_PROGRAM_KEYWORDS_BY_SLUG", {})
    school_kw = getattr(mod, "_KEYWORDS_BY_SCHOOL", {})
    kw = kw_map.get(slug) or (school_kw.get(school) if isinstance(school_kw, dict) else None)
    if hasattr(mod, "_program_content"):
        import inspect
        sig = inspect.signature(mod._program_content)
        params = list(sig.parameters)
        if len(params) == 1:
            return mod._program_content(spec)
        return mod._program_content(school, list(kw or []))
    return None


def get_school_cs(mod, name: str):
    if hasattr(mod, "_school_content"):
        return mod._school_content(name)
    sc = getattr(mod, "_SCHOOL_CONTENT", {})
    return sc.get(name) if isinstance(sc, dict) else None


def is_coverable(p: dict) -> bool:
    pname = (p.get("program_name") or "").lower()
    slug = (p.get("slug") or "").lower()
    dtype = p.get("degree_type", "")
    if dtype not in ("bachelors", "masters", "professional", "doctoral", "phd"):
        return False
    return any(k in pname or k in slug for k in COVERABLE_KEYWORDS)


def audit(name: str) -> dict:
    mod = load(name)
    programs = getattr(mod, "PROGRAMS", [])
    schools = getattr(mod, "SCHOOLS", [])
    reviews = getattr(mod, "_REVIEWS_BY_SLUG", {})
    so = getattr(mod, "SCHOOL_OUTCOMES", {})
    photos = so.get("campus_photos") or []
    std_fn = getattr(mod, "_standard", None)
    omitted_inst = getattr(mod, "_OMITTED_INSTITUTION", [])
    version = None
    if std_fn:
        version = std_fn(omitted_inst).get("version")

    catalog_errors = validate_catalog(programs)
    school_null_cs = 0
    for sc in schools:
        sname = sc["name"] if isinstance(sc, dict) else sc
        cs = get_school_cs(mod, sname)
        if not cs or not cs.get("news_rss"):
            school_null_cs += 1

    prog_null_cs = 0
    coverable = 0
    coverable_no_review = 0
    for p in programs:
        cs = get_program_cs(mod, p)
        if not cs or not cs.get("news_rss"):
            prog_null_cs += 1
        if is_coverable(p):
            coverable += 1
            if p["slug"] not in reviews:
                coverable_no_review += 1

    score = (
        len(catalog_errors) * 1000
        + school_null_cs * 50
        + prog_null_cs * 30
        + coverable_no_review * 5
        + max(0, 4 - len(photos)) * 40
        + (50 if version and version < STANDARD_VERSION else 0)
    )

    return {
        "name": name,
        "score": score,
        "programs": len(programs),
        "schools": len(schools),
        "photos": len(photos),
        "version": version,
        "catalog_errors": len(catalog_errors),
        "school_null_cs": school_null_cs,
        "prog_null_cs": prog_null_cs,
        "coverable": coverable,
        "coverable_no_review": coverable_no_review,
        "reviewed": coverable - coverable_no_review,
    }


def main():
    names = sorted(
        m.name.replace("_profile", "")
        for m in pkgutil.iter_modules(["src/unipaith/data"])
        if m.name.endswith("_profile")
    )
    results = [audit(n) for n in names]
    results.sort(key=lambda r: -r["score"])
    print(f"STANDARD_VERSION={STANDARD_VERSION}\n")
    hdr = f"{'univ':<18} {'score':>6} {'prg':>4} {'sch':>3} {'ph':>2} {'v':>2} {'cat':>3} {'sc_cs':>5} {'pr_cs':>5} {'cov_nr':>6} {'cov_ok':>6}"
    print(hdr)
    for r in results:
        print(
            f"{r['name']:<18} {r['score']:>6} {r['programs']:>4} {r['schools']:>3} {r['photos']:>2} "
            f"{r['version'] or 0:>2} {r['catalog_errors']:>3} {r['school_null_cs']:>5} {r['prog_null_cs']:>5} "
            f"{r['coverable_no_review']:>6} {r['reviewed']:>6}"
        )
    print(f"\nTARGET: {results[0]['name']}")


if __name__ == "__main__":
    main()
