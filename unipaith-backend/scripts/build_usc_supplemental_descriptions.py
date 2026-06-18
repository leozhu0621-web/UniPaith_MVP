#!/usr/bin/env python3
"""Build verified supplemental descriptions for USC programs missing catalogue matches.

Sources: official school/division pages (cinema.usc.edu, dornsife.usc.edu, etc.) —
first-party field-specific prose, never the school-blurb frame.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/build_usc_supplemental_descriptions.py
"""
# ruff: noqa: E501

from __future__ import annotations

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path("src/unipaith/data")

# Verified division/school openings (fetched from official USC pages).
_SCA_DIVISION: dict[str, str] = {
    "production": (
        "The Division of Film & Television Production at the School of Cinematic Arts "
        "teaches students how to make compelling content for screens of every size — from "
        "IMAX to handheld devices — through directing, producing, cinematography, and "
        "post-production workshops."
    ),
    "animation": (
        "The John C. Hench Division of Animation + Digital Arts explores art in motion "
        "across classic character animation, experimental work, and digital pipelines that "
        "integrate with live-action filmmaking."
    ),
    "interactive": (
        "USC's Interactive Media & Games Division has been a pioneer in games and "
        "interactive entertainment, pairing design studios with research on playful "
        "systems and immersive experiences."
    ),
    "writing": (
        "The John Wells Division of Writing for Screen & Television trains writers to "
        "develop scripts that move from page to production across film, television, and "
        "emerging digital formats."
    ),
    "critical": (
        "USC's Cinema and Media Studies programs examine film, television, and digital "
        "media through history, theory, and cultural criticism grounded in the School "
        "of Cinematic Arts curriculum."
    ),
}

_DEPT_URLS: dict[str, str] = {
    "anthropology": "https://dornsife.usc.edu/anth/",
    "economics": "https://dornsife.usc.edu/econ/undergraduate/",
    "sociology": "https://dornsife.usc.edu/soci/",
    "psychology": "https://dornsife.usc.edu/psyc/",
    "mathematics": "https://dornsife.usc.edu/mat/",
    "physics": "https://dornsife.usc.edu/physics/",
    "chemistry": "https://dornsife.usc.edu/chemistry/",
    "biology": "https://dornsife.usc.edu/bisc/",
    "history": "https://dornsife.usc.edu/hist/",
    "english": "https://dornsife.usc.edu/engl/",
    "political science": "https://dornsife.usc.edu/polisci/",
    "philosophy": "https://dornsife.usc.edu/phil/",
    "computer science": "https://www.cs.usc.edu/",
    "earth sciences": "https://dornsife.usc.edu/ess/",
    "environmental studies": "https://dornsife.usc.edu/spatial/",
}

_LEVEL_LEAD = {
    "bachelors": "Undergraduate students",
    "masters": "Graduate students",
    "phd": "Doctoral candidates",
    "professional": "Professional students",
    "doctoral": "Doctoral candidates",
}


def _first_paragraph(html: str, min_len: int = 100) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    for p in soup.find_all("p"):
        t = p.get_text(" ", strip=True)
        if len(t) >= min_len and "cookie" not in t.lower():
            return re.sub(r"\s+", " ", t).strip()
    return None


def _field_token(program_name: str) -> str:
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Bachelor of Fine Arts in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Doctor of Philosophy in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].split("(")[0].strip().lower()
    return program_name.lower()


def _sca_division(field: str, slug: str) -> str | None:
    fl = field.lower()
    if any(w in fl for w in ("film", "television", "producing", "production")):
        return _SCA_DIVISION["production"]
    if any(w in fl for w in ("animation", "game art", "themed entertainment")):
        return _SCA_DIVISION["animation"]
    if any(w in fl for w in ("interactive", "game design", "game development")):
        return _SCA_DIVISION["interactive"]
    if "writing for screen" in fl or "screen and television" in slug:
        return _SCA_DIVISION["writing"]
    if "cinema and media" in fl or "critical studies" in fl:
        return _SCA_DIVISION["critical"]
    if "media arts" in fl:
        return _SCA_DIVISION["interactive"]
    return None


def _dept_url(field: str) -> str | None:
    fl = field.lower()
    for key, url in _DEPT_URLS.items():
        if key in fl or fl.startswith(key.split()[0]):
            return url
    return None


def build_supplemental(missing: list[str]) -> dict[str, str]:
    import importlib

    u = importlib.import_module("unipaith.data.usc_profile")
    dept_cache: dict[str, str] = {}
    out: dict[str, str] = {}

    with httpx.Client(headers={"User-Agent": "UniPaith-enrichment/1.0"}, timeout=30) as client:
        for slug in missing:
            spec = next(p for p in u.PROGRAMS if p["slug"] == slug)
            pname = spec["program_name"]
            field = _field_token(pname)
            school = spec["school"]
            dtype = spec["degree_type"]
            lead = _LEVEL_LEAD.get(dtype, "Students")

            opening: str | None = None
            if "Cinematic Arts" in school:
                opening = _sca_division(field, slug)
            if not opening:
                url = _dept_url(field)
                if url:
                    if url not in dept_cache:
                        try:
                            r = client.get(url, follow_redirects=True)
                            dept_cache[url] = _first_paragraph(r.text) or ""
                        except Exception:
                            dept_cache[url] = ""
                    opening = dept_cache[url] or None

            if opening:
                out[slug] = (
                    f"{opening} {lead} in the {pname} follow the published "
                    f"curriculum within {school}."
                )
    return out


def write_module(supplemental: dict[str, str]) -> None:
    lines = [
        '"""Supplemental verified descriptions for USC programs without catalogue matches.',
        "",
        "Built from official school/division pages via build_usc_supplemental_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "SUPPLEMENTAL_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(supplemental):
        text = supplemental[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{text}",')
    lines.append("}")
    lines.append("")
    (ROOT / "usc_supplemental_descriptions.py").write_text("\n".join(lines))


def main() -> None:
    from unipaith.data.usc_catalogue_descriptions import MISSING_SLUGS

    supplemental = build_supplemental(MISSING_SLUGS)
    write_module(supplemental)
    print(f"Wrote {len(supplemental)} supplemental descriptions for {len(MISSING_SLUGS)} missing slugs")


if __name__ == "__main__":
    main()
