"""Spec 69 §3 — extract program records from a crawled page (deterministic).

Turns a fetched university page into program rows the catalog ingestion (`69`)
can write. Two grounded, deterministic strategies, best-first:

1. **schema.org JSON-LD** (reliable): SEO-optimized `.edu` pages embed
   ``<script type="application/ld+json">`` with ``Course`` /
   ``EducationalOccupationalProgram`` / ``Program`` objects — structured,
   unambiguous, no guessing.
2. **Conservative text patterns** (fallback): a clear degree token + a field
   name, length/sanity-filtered + deduped, so a listing page yields real
   programs and a junk/marketing page yields nothing (never fabricate).

Grounded by construction — every emitted program traces to text on the page. The
Qwen LLM extractor (`63` §5, inert until Qwen is deployed) is the quality upgrade
that slots in above this floor; this rule-based path always runs and never 5xxes.
"""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any

# Degree token → normalized degree (matches the catalog ingester's normalizer).
_DEGREE_TOKENS: dict[str, str] = {
    "phd": "PhD",
    "ph.d.": "PhD",
    "doctor of philosophy": "PhD",
    "doctorate": "PhD",
    "sc.d.": "ScD",
    "master of science": "MS",
    "master of arts": "MA",
    "master of engineering": "MEng",
    "master of business administration": "MBA",
    "master of architecture": "MArch",
    "master of": "MS",
    "m.s.": "MS",
    "m.eng.": "MEng",
    "mba": "MBA",
    "bachelor of science": "BS",
    "bachelor of arts": "BA",
    "bachelor of": "BS",
    "b.s.": "BS",
    "b.a.": "BA",
    "master's": "MS",
    "bachelor's": "BS",
    "certificate": "Certificate",
}

# Field keyword → CIP code (so extracted programs get the matcher's join key).
_FIELD_CIP: dict[str, str] = {
    "computer science": "11.0701",
    "data science": "11.0401",
    "information": "11.0101",
    "electrical engineering": "14.1001",
    "mechanical engineering": "14.1901",
    "civil engineering": "14.0801",
    "chemical engineering": "14.0701",
    "aerospace": "14.0201",
    "aeronautics": "14.0201",
    "materials science": "14.1801",
    "biomedical": "14.0501",
    "engineering": "14.0101",
    "mathematics": "27.0101",
    "physics": "40.0801",
    "chemistry": "40.0501",
    "biology": "26.0101",
    "neuroscience": "26.1501",
    "economics": "45.0601",
    "political science": "45.1001",
    "psychology": "42.0101",
    "business analytics": "52.1301",
    "business administration": "52.0201",
    "management": "52.0201",
    "finance": "52.0801",
    "architecture": "04.0201",
    "urban": "04.0301",
    "public health": "51.2201",
    "nursing": "51.3801",
    "education": "13.0101",
    "law": "22.0101",
    "design": "50.0401",
    "environmental": "03.0104",
}

# A program mention = a degree token directly followed by "in/of". We match only
# up to "in/of" (cursor stops there) and read the field from a short forward
# window — so back-to-back programs joined by "and" aren't swallowed by one match.
_PROG_RE = re.compile(
    r"\b(ph\.?d\.?|doctorate|doctoral|m\.?eng\.?|m\.?s\.?|m\.?a\.?|m\.?b\.?a\.?|mba|"
    r"b\.?s\.?|b\.?a\.?|master'?s?|bachelor'?s?)\s+(?:degree\s+)?(?:in|of)\s+",
    re.IGNORECASE,
)
_DEG_WORD = {
    "phd": "PhD",
    "doctorate": "PhD",
    "doctoral": "PhD",
    "meng": "MEng",
    "ms": "MS",
    "ma": "MA",
    "mba": "MBA",
    "bs": "BS",
    "ba": "BA",
    "master": "MS",
    "masters": "MS",
    "bachelor": "BS",
    "bachelors": "BS",
}


def _deg_word(raw: str) -> str | None:
    return _DEG_WORD.get(re.sub(r"[^a-z]", "", raw.lower()))


def _normalize_degree(token: str) -> str | None:
    t = token.strip().lower().rstrip(".")
    for key, deg in _DEGREE_TOKENS.items():
        if t.startswith(key) or t == key.rstrip("."):
            return deg
    return None


def _cip_for(text: str) -> str | None:
    low = text.lower()
    for kw, cip in _FIELD_CIP.items():
        if kw in low:
            return cip
    return None


def strip_html(html: str) -> str:
    """Cheap HTML → text: drop script/style, tags, collapse whitespace."""
    no_script = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", no_script)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _from_jsonld(html: str) -> list[dict]:
    """Parse schema.org Course / EducationalOccupationalProgram / Program
    JSON-LD blocks — the reliable structured path."""
    out: list[dict] = []
    for block in re.findall(
        r'(?is)<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html
    ):
        try:
            data = json.loads(block.strip())
        except (ValueError, TypeError):
            continue
        nodes = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            nodes = data["@graph"]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            typ = node.get("@type", "")
            types = typ if isinstance(typ, list) else [typ]
            if not any(t in ("Course", "EducationalOccupationalProgram", "Program") for t in types):
                continue
            name = (node.get("name") or "").strip()
            if not name or len(name) > 200:
                continue
            cred = node.get("educationalCredentialAwarded") or node.get("credentialCategory") or ""
            degree = _normalize_degree(str(cred)) if cred else None
            out.append(
                {
                    "program_name": name,
                    "degree_type": degree or "unknown",
                    "cip_code": _cip_for(name),
                    "description": (node.get("description") or "")[:500] or None,
                    "_source": "jsonld",
                }
            )
    return out


def _from_text(text: str, *, max_items: int = 40) -> list[dict]:
    """Conservative text fallback: a degree token directly followed by ``in/of``,
    then the *nearest* known field keyword in the next ~45 chars. Both required, so
    marketing prose yields nothing (grounded, no fabrication)."""
    out: list[dict] = []
    seen: set[str] = set()
    for m in _PROG_RE.finditer(text):
        degree = _deg_word(m.group(1))
        if not degree:
            continue
        window = text[m.end() : m.end() + 45].lower()
        # Nearest field keyword to the degree wins (smallest offset), so
        # "...Science in Computer Science" resolves to "computer science".
        field = cip = None
        best = len(window) + 1
        for kw, code in _FIELD_CIP.items():
            pos = window.find(kw)
            if 0 <= pos < best:
                best, field, cip = pos, kw, code
        if not field:
            continue  # no recognizable field next to the degree → skip
        name = f"{field.title()} ({degree})"
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "program_name": name,
                "degree_type": degree,
                "cip_code": cip,
                "description": None,
                "_source": "text",
            }
        )
        if len(out) >= max_items:
            break
    return out


def extract_programs(html_or_text: str) -> list[dict]:
    """Extract grounded program rows from a fetched page. JSON-LD first (reliable),
    then conservative text patterns. Deduped on (name, degree). Empty when the page
    has no clear program signal — never fabricate."""
    if not html_or_text or not html_or_text.strip():
        return []
    rows = _from_jsonld(html_or_text)
    text = strip_html(html_or_text)
    if len(rows) < 3:  # JSON-LD sparse → supplement with text patterns
        rows.extend(_from_text(text))
    # Dedup on (normalized name, degree); prefer JSON-LD entries.
    deduped: dict[tuple[str, str], dict] = {}
    for r in rows:
        k = (r["program_name"].strip().lower(), r["degree_type"])
        if k not in deduped or r.get("_source") == "jsonld":
            deduped[k] = r
    result: list[dict] = []
    for r in deduped.values():
        r.pop("_source", None)
        result.append(r)
    return result


def to_ingest_rows(programs: list[dict]) -> list[dict[str, Any]]:
    """Shape extracted programs into CatalogIngestService rows (stable external_id
    so a re-crawl updates in place rather than duplicating)."""
    rows: list[dict[str, Any]] = []
    for p in programs:
        name = p["program_name"]
        deg = p.get("degree_type") or "unknown"
        ext = re.sub(r"[^a-z0-9]+", "-", f"{name}-{deg}".lower()).strip("-")[:150]
        rows.append(
            {
                "program_name": name,
                "degree_type": deg,
                "cip_code": p.get("cip_code"),
                "description": p.get("description"),
                "external_id": ext,
            }
        )
    return rows
