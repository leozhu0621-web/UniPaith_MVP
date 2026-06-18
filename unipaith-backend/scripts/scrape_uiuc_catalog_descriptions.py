#!/usr/bin/env python3
"""Scrape verified program descriptions from the UIUC Academic Catalog.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/scrape_uiuc_catalog_descriptions.py

Writes ``src/unipaith/data/uiuc_catalogue_descriptions.py`` keyed by program slug.
Each description is first-party prose from catalog.illinois.edu — never a school-blurb stub.
"""
# ruff: noqa: E501

from __future__ import annotations

import ast
import json
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path("src/unipaith/data")
BASE = "https://catalog.illinois.edu"
MAX_CHARS = 900
MIN_CHARS = 60

_INDEX_PAGES = (
    "/degree-programs/undergraduate_index/",
    "/degree-programs/graduate_index/",
    "/professional-programs/",
)

_SKIP_PATH_PARTS = ("/minors/", "/concentration/", "/cert/", "/foundation", "/honors/")

# Slug -> catalog path (without domain) when automated matching fails.
_URL_OVERRIDES: dict[str, str] = {
    "uiuc-law-jd": "/professional/law-jd/",
    "uiuc-medicine-md": "/professional/medicine-md/",
    "uiuc-veterinary-medicine-dvm": "/professional/dvm-doctor-veterinary-medicine/",
    "uiuc-computer-science-online-mcs": "/graduate/engineering/computer-science-mcs/",
    "uiuc-business-administration-online-mba": "/graduate/bus/business-administration-online-mba/",
    "uiuc-accountancy-imsa-ms": "/graduate/bus/accountancy-ms/",
    "uiuc-management-imsm-ms": "/graduate/bus/management-ms/",
    "uiuc-foundation": "/undergraduate/faa/art-design-bfa/foundation/",
    "uiuc-artist-diploma-music": "/undergraduate/faa/music-bm/artist-diploma/",
    "uiuc-comparative-literature": "/undergraduate/las/comparative-literature-bslas/",
    "uiuc-individual-plans-study": "/undergraduate/las/individual-plans-study-bslas/",
    "uiuc-honors": "/undergraduate/las/integrative-biology-bslas/",
    "uiuc-animal-sciences-mansc": "/graduate/aces/animal-sciences-ms/",
    "uiuc-agricultural-biological-engineering-bs-agricultural-engineering-agricultural-science-bsag": (
        "/undergraduate/engineering/agricultural-biological-engineering-bs/"
    ),
}


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        last_period = cut.rfind(". ")
        if last_period >= MIN_CHARS:
            text = cut[: last_period + 1]
        else:
            text = cut.rstrip(" ,;") + "."
    return text


def extract_description(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    for h2 in soup.find_all("h2"):
        if h2.get_text(strip=True).lower() != "overview":
            continue
        parts: list[str] = []
        for sib in h2.find_next_siblings():
            if sib.name == "h2":
                break
            if sib.name == "p":
                t = sib.get_text(" ", strip=True)
                if t:
                    parts.append(t)
        if parts:
            joined = _clean(" ".join(parts))
            if len(joined) >= MIN_CHARS:
                return joined

    h1 = soup.find("h1")
    if not h1:
        return None
    skip = (
        "similar pages",
        "send page to printer",
        "print this page",
        "2026-2027 catalog",
        "search catalog",
        "was not found",
        "university requirements",
        "for the degree of",
        "students pursuing this major select",
    )
    for p in h1.find_all_next("p", limit=12):
        t = p.get_text(" ", strip=True)
        if len(t) < MIN_CHARS:
            continue
        low = t.lower()
        if any(s in low for s in skip):
            continue
        return _clean(t)
    return None


def fetch_description(client: httpx.Client, path: str) -> tuple[str | None, str | None]:
    url = BASE + path if path.startswith("/") else path
    try:
        r = client.get(url, follow_redirects=True, timeout=30.0)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else None
        desc = extract_description(r.text)
        return title, desc
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL {path}: {exc}")
        return None, None


def _is_degree_url(path: str) -> bool:
    if not path.startswith(("/undergraduate/", "/graduate/", "/professional/")):
        return False
    if any(x in path for x in _SKIP_PATH_PARTS):
        return False
    parts = [p for p in path.strip("/").split("/") if p]
    # undergraduate/college/program OR professional/law-jd
    if parts[0] == "professional":
        return len(parts) == 2
    return len(parts) == 3


def collect_catalog_paths(client: httpx.Client) -> dict[str, str]:
    """Map normalized last-segment -> full catalog path."""
    out: dict[str, str] = {}
    for index in _INDEX_PAGES:
        try:
            r = client.get(BASE + index, follow_redirects=True, timeout=30.0)
            r.raise_for_status()
            for href in re.findall(r'href="(/[^"]+)"', r.text):
                if _is_degree_url(href):
                    key = href.rstrip("/").split("/")[-1]
                    out[key] = href if href.endswith("/") else href + "/"
            print(f"  {index}: {len(out)} degree paths so far")
        except Exception as exc:  # noqa: BLE001
            print(f"  index FAIL {index}: {exc}")
    return out


def load_catalog_specs() -> list[dict]:
    text = (ROOT / "uiuc_profile.py").read_text()
    marker = "_CATALOG: list[tuple] = "
    start = text.index(marker)
    list_start = start + len(marker)
    stop = text.index("\n\n# Slugs whose program_name", list_start)
    list_end = text.rindex("]", list_start, stop) + 1
    catalog = ast.literal_eval(text[list_start:list_end])
    out: list[dict] = []
    for slug, sk, name, dtype, dept, fmt, dur in catalog:
        out.append(
            {
                "slug": slug,
                "school_key": sk,
                "field": name,
                "degree_type": dtype,
                "delivery_format": fmt,
            }
        )
    if len(out) < 400:
        raise ValueError(f"Expected ~419 catalog rows, parsed {len(out)}")
    return out


def _normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _token_score(a: str, b: str) -> float:
    ta, tb = set(_normalize(a).split()), set(_normalize(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def match_path(slug: str, paths_by_tail: dict[str, str]) -> str | None:
    if slug in _URL_OVERRIDES:
        return _URL_OVERRIDES[slug]
    tail = slug[len("uiuc-") :]
    if tail in paths_by_tail:
        return paths_by_tail[tail]
    # Try dropping redundant middle segments for long slugs.
    candidates = [
        p for k, p in paths_by_tail.items() if tail.endswith(k) or k in tail or tail in k
    ]
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        return max(candidates, key=lambda p: _token_score(tail, p.rstrip("/").split("/")[-1]))
    loose = [
        (p, _token_score(tail, k))
        for k, p in paths_by_tail.items()
        if _token_score(tail, k) >= 0.45
    ]
    if loose:
        return max(loose, key=lambda x: x[1])[0]
    return None


def write_module(descriptions: dict[str, str], missing: list[str]) -> None:
    lines = [
        '"""Verified program descriptions scraped from the UIUC Academic Catalog.',
        "",
        "Each entry is first-party prose from catalog.illinois.edu.",
        "Regenerate via scripts/scrape_uiuc_catalog_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "CATALOGUE_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(descriptions):
        text = descriptions[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{text}",')
    lines.append("}")
    lines.append("")
    lines.append(f"MISSING_SLUGS: list[str] = {missing!r}")
    lines.append("")
    (ROOT / "uiuc_catalogue_descriptions.py").write_text("\n".join(lines))


CACHE_PATH = Path("src/unipaith/data/.uiuc_catalogue_cache.json")


def main() -> None:
    specs = load_catalog_specs()
    descriptions: dict[str, str] = {}
    missing: list[str] = []
    cache: dict[str, tuple[str | None, str | None]] = {}

    with httpx.Client(headers={"User-Agent": "UniPaith-enrichment/1.0"}) as client:
        if CACHE_PATH.exists():
            raw = json.loads(CACHE_PATH.read_text())
            cache = {k: (v[0], v[1]) for k, v in raw.items()}
            print(f"Loaded {len(cache)} cached catalogue entries")

        paths_by_tail = collect_catalog_paths(client)
        print(f"Collected {len(paths_by_tail)} degree catalog paths")

        for i, spec in enumerate(specs):
            slug = spec["slug"]
            path = match_path(slug, paths_by_tail)
            if not path:
                missing.append(slug)
                continue
            if path in cache and cache[path][1]:
                descriptions[slug] = cache[path][1]
                continue
            title, desc = fetch_description(client, path)
            cache[path] = (title, desc)
            if desc:
                descriptions[slug] = desc
            else:
                missing.append(slug)
                print(f"  no description: {slug} -> {path} ({title})")
            if (i + 1) % 40 == 0:
                print(f"  {i + 1}/{len(specs)} ({len(descriptions)} matched)")
            time.sleep(0.06)

        CACHE_PATH.write_text(
            json.dumps({k: [v[0], v[1]] for k, v in cache.items()}, ensure_ascii=False)
        )

    write_module(descriptions, missing)
    print(
        f"Done: {len(descriptions)} matched descriptions, {len(missing)} missing "
        "→ uiuc_catalogue_descriptions.py"
    )
    if missing[:15]:
        print("Sample missing:", missing[:15])


if __name__ == "__main__":
    main()
