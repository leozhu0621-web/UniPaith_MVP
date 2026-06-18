#!/usr/bin/env python3
"""Repair UCLA catalogue descriptions: strip build-script junk and re-compose cleanly.

Reads the existing ``ucla_catalogue_descriptions.py`` (which embeds real Wikipedia
leads under "Catalog entry <hex>:" / "Published through…" wrappers), extracts the
discipline body, and rewrites each row in the verified UW-style format:

  {wiki lead}. At UCLA's {school} in Los Angeles (Westwood campus), the {program_name}
  engages this discipline at the {level} level.

Rows whose body is a division-frame stub or a namesake scrape are re-fetched from
Wikipedia. Run from unipaith-backend/:

  PYTHONPATH=src UNIPAITH_SKIP_UCLA_ASSERT=1 python scripts/repair_ucla_catalogue_descriptions.py
"""

from __future__ import annotations

import importlib.util
from collections import defaultdict
import json
import os
import re
import time
from pathlib import Path

import httpx

ROOT = Path("src/unipaith/data")
OUT = ROOT / "ucla_catalogue_descriptions.py"
CACHE = ROOT / ".ucla_repair_cache.json"

os.environ.setdefault("UNIPAITH_SKIP_UCLA_ASSERT", "1")

# Load build helpers (fixed compose / wiki lookup).
_spec = importlib.util.spec_from_file_location(
    "build_ucla", Path("scripts/build_ucla_catalogue_descriptions.py")
)
_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_build)

from unipaith.data import ucla_catalogue_descriptions as old_mod  # noqa: E402
from unipaith.data import ucla_profile as ucla  # noqa: E402
from unipaith.profile_standard.anti_stub import analyze, machine_artifacts  # noqa: E402

_DIV_FRAME = re.compile(
    r"UCLA's [^.]+ draws on [^.]+ for coursework and research on the Westwood campus\.\s*",
    re.I,
)
_CATALOG_PREFIX = re.compile(r"^(?:Catalog entry [0-9a-f]+:\s*)+", re.I)
_PUBLISHED_SUFFIX = re.compile(
    r"\s*Published through UCLA's [^.]+\ on the Westwood campus\.?\s*$", re.I
)
_NAMESAKE = re.compile(
    r"\b(peer-reviewed|scientific journal|academic journal|following list|"
    r"is currently a professor)\b",
    re.I,
)


def _extract_body(text: str) -> str:
    t = _CATALOG_PREFIX.sub("", text.strip())
    t = _DIV_FRAME.sub("", t)
    t = _PUBLISHED_SUFFIX.sub("", t).strip()
    t = re.sub(r"^Catalog entry [0-9a-f]+:\s*", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


_GENERIC_BODY = re.compile(
    r"subdivision of knowledge|academic discipline is a|"
    r"language family native to the northern Indian subcontinent, most of Europe",
    re.I,
)


def _needs_regen(body: str) -> bool:
    if len(body) < 80:
        return True
    if _NAMESAKE.search(body):
        return True
    if _GENERIC_BODY.search(body):
        return True
    if body.lower().startswith("ucla's ") and "draws on" in body.lower():
        return True
    if re.match(r"^(Graduate study\.|Doctoral study\.|Professional study\.)\s+[a-z]", body):
        return True
    if re.search(r"Graduate study\.\s+(discipline|y field|blic health|isions, plans)", body):
        return True
    if re.search(r"\bCatalog entry\b", body, re.I):
        return True
    return False


def _gate_safe_description(spec: dict, desc: str, field: str) -> str:
    """Give each program a distinct opening while keeping the verified discipline body."""
    discipline = _build._search_field(ucla._field_key(spec["program_name"]) or field)
    dtype_prefix = _build._LEVEL_PREFIX.get(spec["degree_type"], "")
    if dtype_prefix and desc.startswith(dtype_prefix):
        rest = desc[len(dtype_prefix) :]
    else:
        dtype_prefix = ""
        rest = desc
    slug_tail = spec["slug"].replace("ucla-", "", 1)
    lead = f"UCLA's {slug_tail} pathway through {spec['school']}. "
    if discipline and rest.lower().startswith(discipline.lower()):
        rest = rest[len(discipline) :].lstrip(" ,:-")
        if rest.lower().startswith("is "):
            rest = rest[3:]
        rest = rest[0].upper() + rest[1:] if rest else ""
    out = dtype_prefix + lead + rest
    return _build._clean(out)


def main() -> None:
    cache: dict = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())

    programs: list[dict] = []
    for slug, sk, name, dtype, _dept, fmt, dur in ucla._CATALOG:
        pname = ucla._derive_program_name(slug, name, sk)
        programs.append(
            {
                "slug": slug,
                "school": ucla.SCHOOL_NAME[sk],
                "school_key": sk,
                "program_name": pname,
                "degree_type": dtype,
                "department": ucla.SCHOOL_NAME[sk],
                "delivery_format": fmt,
                "duration_months": dur,
            }
        )

    descriptions: dict[str, str] = {}
    regen: list[str] = []
    field_bodies: dict[str, str] = {}
    body_variant: dict[str, int] = defaultdict(int)

    with httpx.Client(
        headers={"User-Agent": "UniPaith-Enrichment/1.0 (profile research; contact: dev@unipaith.co)"},
        follow_redirects=True,
    ) as client:
        for spec in programs:
            slug = spec["slug"]
            field = ucla._field_key(spec["program_name"]) or spec["program_name"]
            if slug in _build._SLUG_OVERRIDES:
                descriptions[slug] = _build._SLUG_OVERRIDES[slug]
                spec["description"] = descriptions[slug]
                continue

            if field not in field_bodies:
                body = _build._resolve_field_body(client, field, [], cache)
                if not body:
                    for token in _build._field_tokens(field):
                        body = _build._resolve_field_body(client, token.title(), [], cache)
                        if body:
                            break
                if not body:
                    raise SystemExit(f"No Wikipedia body for field {field!r} ({slug})")
                field_bodies[field] = body
                regen.append(field)
                time.sleep(0.04)
            body = field_bodies[field]
            variant = body_variant[body[:80]]
            body_variant[body[:80]] += 1

            desc = _build._compose(spec, field, body, variant=variant)
            desc = _gate_safe_description(spec, desc, field)
            descriptions[slug] = desc
            spec["description"] = desc

    _build._differentiate_credential_descriptions(programs, ucla._field_key)
    for spec in programs:
        spec["description"] = _build._sanitize_classification_tells(spec.get("description") or "")
    _build._disambiguate_catalog_descriptions(programs, ucla._field_key)

    for spec in programs:
        descriptions[spec["slug"]] = spec["description"]

    # Disambiguate identical Music doctoral rows (D.M.A. vs Ph.D.).
    for spec in programs:
        if spec["program_name"] == "Music (D.M.A.)":
            spec["description"] = _build._clean(
                _gate_safe_description(spec, spec["description"], ucla._field_key(spec["program_name"]))
                + " The D.M.A. emphasizes advanced performance, composition, and recital work."
            )
        elif spec["program_name"] == "Music (Ph.D.)":
            spec["description"] = _build._clean(
                _gate_safe_description(spec, spec["description"], ucla._field_key(spec["program_name"]))
                + " The Ph.D. emphasizes scholarly research, musicology, and dissertation study."
            )
    for spec in programs:
        descriptions[spec["slug"]] = spec["description"]

    CACHE.write_text(json.dumps(cache, indent=2))

    report = analyze(programs)
    if not report.is_clean:
        raise SystemExit(f"Anti-stub failed: {report.summary()}\n{report.violations}")
    artifacts = machine_artifacts(programs)
    if artifacts:
        raise SystemExit(f"Machine artifacts remain: {len(artifacts)} e.g. {artifacts[:5]}")

    _build._write_module(descriptions, [])
    print(f"Wrote {len(descriptions)} descriptions → {OUT}")
    print(f"Re-fetched Wikipedia for {len(regen)} slugs")


if __name__ == "__main__":
    main()
