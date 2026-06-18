#!/usr/bin/env python3
"""Scrape verified program descriptions from NYU Bulletin pages.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/scrape_nyu_bulletin_descriptions.py

Writes ``src/unipaith/data/nyu_bulletin_descriptions.py`` keyed by program slug.
Each description is the full Program Description section from the bulletin — verified
first-party text, never a school-blurb stub.
"""
# ruff: noqa: E501

from __future__ import annotations

import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path("src/unipaith/data")
BASE = "https://bulletins.nyu.edu"
MAX_CHARS = 900
MIN_CHARS = 80


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
        if h2.get_text(strip=True).lower() != "program description":
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
            return _clean(" ".join(parts))
    for p in soup.find_all("p"):
        t = p.get_text(" ", strip=True)
        if len(t) >= MIN_CHARS and "application fee" not in t.lower():
            return _clean(t)
    return None


def fetch_description(client: httpx.Client, url: str) -> str | None:
    try:
        r = client.get(url, follow_redirects=True, timeout=30.0)
        r.raise_for_status()
        return extract_description(r.text)
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL {url}: {exc}")
        return None


def load_catalog_urls() -> list[tuple[str, str]]:
    """Parse bulletin paths from nyu_profile._CATALOG without importing the module."""
    text = (ROOT / "nyu_profile.py").read_text()
    start = text.index("_CATALOG:")
    stop = text.index("_FLAGSHIP =", start)
    block = text[start:stop]
    pattern = re.compile(
        r'"([a-z0-9-]+)"\s*,\s*_[A-Z]+\s*,\s*"[^"]+"\s*,\s*"[^"]+"\s*,\s*"([^"]+)"\s*,\s*"([^"]*)"'
    )
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for slug, path, suffix in pattern.findall(block):
        db_slug = f"nyu-{slug}{suffix}"
        if db_slug in seen:
            continue
        seen.add(db_slug)
        url = path if path.startswith("http") else BASE + path
        out.append((db_slug, url))
    if len(out) < 500:
        raise ValueError(f"Expected ~507 catalog URLs, parsed {len(out)}")
    return out


def write_module(descriptions: dict[str, str], missing: list[str]) -> None:
    lines = [
        '"""Verified program descriptions scraped from NYU Bulletin pages.',
        "",
        "Each entry is the Program Description section from bulletins.nyu.edu.",
        "Regenerate via scripts/scrape_nyu_bulletin_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "BULLETIN_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(descriptions):
        text = descriptions[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{text}",')
    lines.append("}")
    lines.append("")
    lines.append(f"MISSING_SLUGS: list[str] = {missing!r}")
    lines.append("")
    (ROOT / "nyu_bulletin_descriptions.py").write_text("\n".join(lines))


def main() -> None:
    descriptions: dict[str, str] = {}
    missing: list[str] = []
    catalog = load_catalog_urls()
    print(f"Scraping {len(catalog)} bulletin pages…")
    with httpx.Client(headers={"User-Agent": "UniPaith-enrichment/1.0"}) as client:
        for i, (slug, url) in enumerate(catalog):
            desc = fetch_description(client, url)
            if desc:
                descriptions[slug] = desc
            else:
                missing.append(slug)
            if (i + 1) % 25 == 0:
                print(
                    f"  {i + 1}/{len(catalog)} "
                    f"({len(descriptions)} ok, {len(missing)} missing)"
                )
            time.sleep(0.15)
    write_module(descriptions, missing)
    print(
        f"Done: {len(descriptions)} descriptions, {len(missing)} missing "
        "→ nyu_bulletin_descriptions.py"
    )


if __name__ == "__main__":
    main()
