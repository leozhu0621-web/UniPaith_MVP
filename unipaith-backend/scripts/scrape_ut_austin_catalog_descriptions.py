#!/usr/bin/env python3
"""Scrape verified program descriptions from the UT Austin Academic Catalog.

Run from unipaith-backend/:
  PYTHONPATH=src .venv/bin/python scripts/scrape_ut_austin_catalog_descriptions.py

Writes ``src/unipaith/data/ut_austin_catalogue_descriptions.py`` keyed by program slug.
Each description is first-party prose from catalog.utexas.edu (CourseLeaf) — never a
school-blurb stub. UT Austin's catalog is CourseLeaf (same engine as UIUC's
catalog.illinois.edu), so the index/program crawl mirrors the UIUC scraper.
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
BASE = "https://catalog.utexas.edu"
MAX_CHARS = 900
MIN_CHARS = 80
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) UniPaith-enrichment/1.0"}

_INDEX_PAGES = ("/undergraduate/azindex/", "/graduate/azindex/")

# Lead-paragraph boilerplate that is NOT a program description (UT Austin grad pages
# open with campus/mailing address, office hours, faculty rosters, etc.).
_SKIP_LEAD = (
    "campus address",
    "mailing address",
    "campus mail code",
    "phone (",
    "fax (",
    "mission is to create",
    "similar pages",
    "print option",
    "send page to printer",
    "for the degree of",
    "university requirements",
    "served on the graduate studies committee",
    "graduate studies committee (gsc)",
    "the following faculty",
    "for more information, visit",
    "office of",
    "was not found",
    "students pursuing this",
    "the prerequisite for",
    "admission to the",
    "to be considered for admission",
    "applicants must",
    "http://",
    "https://",
)

# Slug tail -> explicit catalog path when token matching is unreliable.
_URL_OVERRIDES: dict[str, str] = {
    "business-administration-mba": "/graduate/areas-of-study/business/business-administration/",
    "law-jd": "/law/",
    "medicine-md": "/medical/",
    "computer-science-bsa": "/undergraduate/natural-sciences/degrees-and-programs/ba-computer-science/",
    "computer-science-bs": "/undergraduate/natural-sciences/degrees-and-programs/bs-computer-science/",
}


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.{2,}", ".", text)
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        last_period = cut.rfind(". ")
        text = cut[: last_period + 1] if last_period >= MIN_CHARS else cut.rstrip(" ,;") + "."
    return text


# Paragraphs that are NOT a program description, however many keywords they contain:
# administrative / facilities / library / requirements boilerplate.
_REJECT = (
    "campus address", "mailing address", "campus mail code", "phone (", "fax (",
    "mission is to create", "similar pages", "print option", "send page to printer",
    "the pdf will include", "for the degree of", "university requirements",
    "served on the graduate studies committee", "graduate studies committee",
    "the following faculty", "was not found", "to be awarded the degree",
    "the candidate must complete", "semester hours", "semester credit hours",
    "facilities for", "physical facilities", "research facilities", "teaching and research facilities",
    "research laboratories are available", "laboratories are available",
    "uses none of the physical facilities", "is located in the", "is located on",
    "is housed in the", "are housed in", "perry-casta", "harry ransom",
    "the fine arts library", "open-shelf", "university libraries contain",
    "library contains", "library system", "rare and unique materials",
    "dolph briscoe", "mcdonald observatory", "graduate handbook", "handbook",
    "must participate in an approved study abroad", "box.com", "consult the graduate advisor",
    "for descriptions of these programs", "for more information, visit", "office of",
    "http://", "https://", "computing systems, and research centers",
    # admin / requirements / facilities boilerplate that mimics prose
    "laptop", "computer lab", "is reserved for", "24 hours a day", "are required to have",
    "statement of intent", "letters of reference", "letter of recommendation",
    "all applicants are required", "applicants must", "applicant should have",
    "courses which may be used", "requirement 2", "requirement 1",
    "visual and performing arts requirement", "bachelor of science in education degree",
    "faculty are drawn from", "is funded by", "grant #", "the goal of", "core facilities",
    "instrumentation", "the canfield", "excellent resources to serve",
    "the university offers excellent", "access to", "the major collections",
    "have an array of facilities", "an array of facilities", "outstanding opportunities for research",
    "state-of-the-art", "shared resource", "the program is reserved",
    # admissions / process boilerplate
    "admission to the", "admission decision", "admission is", "holistic review",
    "test scores", "personal statement", "review process", "gre ", "deadline",
    "is extremely competitive", "other facilities", "facilities of interest",
    "center for international business", "benson latin american",
    "students must enter", "program office", "academic advising", "student services",
    "contact information", "given on the top", "this page", "students must apply",
    "are admitted", "is admitted", "enrollment", "students may enter", "must be completed",
    "applicants who", "to apply", "application deadline", "credit hours",
)

# Descriptive openers that mark a real program/field overview (reward these).
_GOOD_START = re.compile(
    r"^(the (department|program|graduate program|undergraduate program|school|college|major|field|study|m\.?s\.?|ph\.?d\.?)\b"
    r"|[a-z][a-z &/-]+ (is|are|offers|provides|prepares|combines|explores|examines|focuses|studies|trains|integrates|encompasses)\b"
    r"|graduate study in|graduate work in|the (b\.?[as]\.?|bachelor|master|doctor))",
    re.I,
)
_GOOD_KW = re.compile(
    r"\b(focuses on|designed to|prepares (students|graduates)|study of|the discipline|core areas|"
    r"offers (graduate|undergraduate) study|areas of (concentration|specialization|study|research)|"
    r"interdisciplinary|curriculum (is|emphasizes|provides)|trains|the field of)\b",
    re.I,
)


def _para_score(t: str) -> float:
    low = t.lower()
    if any(s in low for s in _REJECT):
        return -1.0
    score = 0.0
    if _GOOD_START.search(t):
        score += 2.0
    score += 0.6 * len(_GOOD_KW.findall(t))
    # prefer substantial prose; penalize digit-heavy (requirements/credit tables)
    digits = sum(c.isdigit() for c in t)
    if digits > 8:
        score -= 1.0
    if len(t) >= 160:
        score += 0.5
    return score


def extract_paragraphs(html: str, limit: int = 8) -> list[str]:
    """Ranked list of distinct descriptive paragraphs from a catalog page.

    UT's graduate area pages describe the field once plus per-concentration / research
    paragraphs; returning a ranked list lets co-located credential siblings each take a
    DISTINCT real paragraph instead of sharing one (which the anti-stub gate rejects).
    """
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    nodes = h1.find_all_next("p", limit=60) if h1 else soup.find_all("p", limit=60)
    out: list[str] = []
    seen: set[str] = set()
    for p in nodes:
        t = p.get_text(" ", strip=True)
        if len(t) < MIN_CHARS:
            continue
        if _para_score(t) <= 0:
            continue
        cleaned = _clean(t)
        key = cleaned[:80].lower()
        if key in seen or len(cleaned) < MIN_CHARS:
            continue
        seen.add(key)
        out.append(cleaned)
        if len(out) >= limit:
            break
    return out


def extract_description(html: str) -> str | None:
    paras = extract_paragraphs(html, limit=1)
    return paras[0] if paras else None


def fetch_html(client: httpx.Client, path: str) -> str | None:
    url = BASE + path if path.startswith("/") else path
    for attempt in range(3):
        try:
            r = client.get(url, follow_redirects=True, timeout=30.0)
            if r.status_code == 200:
                return r.text
            return None
        except Exception:  # noqa: BLE001
            time.sleep(0.5 * (attempt + 1))
    return None


def _is_degree_url(path: str) -> bool:
    """A program/major page lives under a college's degrees-and-programs/areas-of-study
    subtree at depth 4 or 5 (BBA/BS majors nest one level deeper)."""
    parts = [p for p in path.strip("/").split("/") if p]
    if "/courses/" in path or path.endswith("/courses/"):
        return False
    # "sugg-*" / "suggested-arrangement-*" pages are course-sequence tables, no prose.
    if parts and (parts[-1].startswith("sugg-") or "suggested-arrangement" in parts[-1]):
        return False
    if path.startswith("/undergraduate/") and "degrees-and-programs" in parts:
        return 4 <= len(parts) <= 5 and parts[-1] != "degrees-and-programs"
    if path.startswith("/graduate/areas-of-study/"):
        return 4 <= len(parts) <= 5
    return False


def _links_in(client: httpx.Client, path: str) -> set[str]:
    r = None
    for attempt in range(3):
        try:
            r = client.get(BASE + path, follow_redirects=True, timeout=30.0)
            r.raise_for_status()
            break
        except Exception:  # noqa: BLE001
            time.sleep(0.5 * (attempt + 1))
    if r is None or r.status_code != 200:
        return set()
    out = set()
    for href in re.findall(r'href="(/[^"]+)"', r.text):
        href = href.split("#")[0].split("?")[0]
        if not href.endswith("/"):
            href += "/"
        if href.startswith(path) and href != path:
            out.add(href)
    return out


def collect_catalog_paths(client: httpx.Client) -> list[str]:
    out: set[str] = set()
    # Undergrad: crawl each college's degrees-and-programs index + one level deeper.
    ug = _links_in(client, "/undergraduate/")
    ug_colleges = [p for p in ug if len(p.strip("/").split("/")) == 2]
    grad_colleges = [
        p for p in _links_in(client, "/graduate/areas-of-study/")
        if len(p.strip("/").split("/")) == 3
    ]
    roots = [c + "degrees-and-programs/" for c in ug_colleges] + grad_colleges
    for root in roots:
        depth4 = _links_in(client, root)
        for href in depth4:
            if _is_degree_url(href):
                out.add(href)
            # one level deeper for nested majors (BBA/BS/areas-of-study programs)
            for sub in _links_in(client, href):
                if _is_degree_url(sub):
                    out.add(sub)
        time.sleep(0.03)
    # azindex as a backstop
    for index in _INDEX_PAGES:
        for href in _links_in(client, index):
            if _is_degree_url(href):
                out.add(href)
    print(f"  collected {len(out)} degree paths from {len(roots)} college roots")
    return sorted(out)


def load_catalog_specs() -> list[dict]:
    text = (ROOT / "ut_austin_profile.py").read_text()
    marker = "_CATALOG: list[tuple] = "
    start = text.index(marker)
    list_start = start + len(marker)
    list_end = text.index("\n]\n", list_start) + 2
    catalog = ast.literal_eval(text[list_start:list_end])
    out: list[dict] = []
    for slug, sk, name, dtype, _dept, fmt, _dur in catalog:
        out.append(
            {"slug": slug, "school_key": sk, "field": name, "degree_type": dtype, "fmt": fmt}
        )
    if len(out) < 300:
        raise ValueError(f"Expected ~338 catalog rows, parsed {len(out)}")
    return out


_DEGREE_HINT = {
    "bachelors": ("ba", "bs", "bsa", "barch", "bba", "bfa", "bsn", "bsed", "bsme", "bspe"),
    "masters": ("ma", "ms", "mfa", "mba", "mpa", "march", "msn", "med", "mssw", "mpaff"),
    "phd": ("phd", "dma", "edd", "aud", "dnp"),
    "professional": ("jd", "md", "pharmd"),
}


def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\bgraduate\b|\bundergraduate\b|\bdegrees and programs\b|\bareas of study\b", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _field_tokens(field: str) -> set[str]:
    stop = {"and", "of", "the", "in", "studies", "science", "sciences", "arts", "a"}
    return {t for t in _norm(field).split() if t not in stop and len(t) > 2}


def _score(field: str, dtype: str, path: str) -> float:
    is_ug = "degrees-and-programs" in path
    # degree-level gate: undergrad rows match undergrad paths, grad rows match grad paths
    if dtype == "bachelors" and not is_ug:
        return 0.0
    if dtype != "bachelors" and is_ug:
        return 0.0
    # Score the leaf segment, but also consider the last two segments for nested majors.
    segs = path.rstrip("/").split("/")
    leaf = segs[-1]
    ftoks = _field_tokens(field)
    if not ftoks:
        return 0.0
    best = 0.0
    for cand in (leaf, " ".join(segs[-2:])):
        ttoks = {t for t in _norm(cand).split() if len(t) > 2}
        if not ttoks:
            continue
        inter = len(ftoks & ttoks)
        # asymmetric: reward covering the field tokens (leaf can carry extra "bs"/credential)
        cov = inter / len(ftoks)
        jac = inter / len(ftoks | ttoks)
        best = max(best, 0.6 * cov + 0.4 * jac)
    return best


def match_path(spec: dict, paths: list[str]) -> str | None:
    tail = spec["slug"][len("ut-austin-") :]
    if tail in _URL_OVERRIDES:
        return _URL_OVERRIDES[tail]
    field, dtype = spec["field"], spec["degree_type"]
    scored = [(p, _score(field, dtype, p)) for p in paths]
    scored = [(p, s) for p, s in scored if s > 0]
    if not scored:
        return None
    top = max(s for _, s in scored)
    # Among (near-)tied best scores, prefer the most specific real program page
    # (shallower grouping pages like "bachelor-of-arts-plan-i" lose to the leaf major).
    tied = [p for p, s in scored if s >= top - 1e-9]
    best = min(tied, key=lambda p: (len(p.rstrip("/").split("/")), p))
    return best if top >= 0.34 else None


def write_module(descriptions: dict[str, str], missing: list[str]) -> None:
    lines = [
        '"""Verified program descriptions scraped from the UT Austin Academic Catalog.',
        "",
        "Each entry is first-party prose from catalog.utexas.edu (CourseLeaf).",
        "Regenerate via scripts/scrape_ut_austin_catalog_descriptions.py.",
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
    lines.append(f"MISSING_SLUGS: list[str] = {sorted(missing)!r}")
    lines.append("")
    (ROOT / "ut_austin_catalogue_descriptions.py").write_text("\n".join(lines))


CACHE_PATH = ROOT / ".ut_austin_html_cache.json"


def main() -> None:
    specs = load_catalog_specs()
    descriptions: dict[str, str] = {}
    missing: list[str] = []
    html_cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        html_cache = json.loads(CACHE_PATH.read_text())
        print(f"Loaded {len(html_cache)} cached HTML pages")

    with httpx.Client(headers=HEADERS) as client:
        # Resolve each slug to its catalog path (collect paths only if not fully cached).
        paths = sorted(html_cache) if html_cache else collect_catalog_paths(client)
        if not html_cache:
            print(f"Collected {len(paths)} degree catalog paths")
        slug_path = {}
        for spec in specs:
            p = match_path(spec, paths)
            if p:
                slug_path[spec["slug"]] = p

        # Fetch HTML for every matched path.
        for i, path in enumerate(sorted(set(slug_path.values()))):
            if path not in html_cache:
                html_cache[path] = fetch_html(client, path) or ""
                time.sleep(0.05)
                if (i + 1) % 60 == 0:
                    CACHE_PATH.write_text(json.dumps(html_cache, ensure_ascii=False))

        # Group slugs that resolved to the SAME page; assign each a DISTINCT real
        # paragraph where the page has enough (credential order: bachelors, masters,
        # professional, phd). When the page offers fewer distinct paragraphs than
        # siblings (UT groups all degrees of a field on one area page), the extras
        # reuse the best paragraph — the profile's credential-lead resolver then makes
        # each sibling's leading body distinct from real field prose.
        cred_order = {"bachelors": 0, "masters": 1, "professional": 2, "phd": 3}
        path_slugs: dict[str, list[dict]] = {}
        for spec in specs:
            p = slug_path.get(spec["slug"])
            if p:
                path_slugs.setdefault(p, []).append(spec)
        for path, group in path_slugs.items():
            paras = extract_paragraphs(html_cache.get(path, ""))
            if not paras:
                continue
            group = sorted(group, key=lambda s: (cred_order.get(s["degree_type"], 9), s["slug"]))
            for idx, spec in enumerate(group):
                descriptions[spec["slug"]] = paras[idx] if idx < len(paras) else paras[0]
        for spec in specs:
            if spec["slug"] not in descriptions:
                missing.append(spec["slug"])

    CACHE_PATH.write_text(json.dumps(html_cache, ensure_ascii=False))
    write_module(descriptions, missing)
    print(f"Done: {len(descriptions)} matched, {len(missing)} missing → ut_austin_catalogue_descriptions.py")
    print("Sample missing:", missing[:25])


if __name__ == "__main__":
    main()
