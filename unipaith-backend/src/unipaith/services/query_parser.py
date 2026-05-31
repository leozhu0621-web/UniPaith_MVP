"""Rule-based natural-language → constraint-chip parser (spec 10).

This is BOTH the flag-off default AND the fallback when the
DiscoveryQueryInterpreter LLM agent is disabled, errors, or times out. It is
deterministic (no randomness, no network) so it can run anywhere and is fully
unit-testable against spec 10 §15.

It is intentionally conservative: it extracts only constraints it can match
with reasonable confidence and leaves nuance to the LLM agent. Anything it
can't categorize is left out (the residual text is still usable as the FTS
query upstream).
"""

from __future__ import annotations

import re

from unipaith.schemas.search import ConstraintCategory, ConstraintChip

# ── Degree level ─────────────────────────────────────────────────────────────
# Ordered: doctorate before master so "phd" doesn't get swallowed. Canonical
# values match the agent prompt; SearchService normalizes them to DB tokens.
_DEGREE_PATTERNS: list[tuple[str, str, str]] = [
    (r"\b(ph\.?\s?d|doctoral|doctorate)\b", "doctorate", "Doctorate"),
    (r"\b(master'?s?|m\.?s\.?|m\.?a\.?|mba|m\.?eng|meng)\b", "master", "Master's"),
    (r"\b(bachelor'?s?|b\.?s\.?|b\.?a\.?|undergrad(?:uate)?)\b", "bachelor", "Bachelor's"),
    (r"\b(associate'?s?)\b", "associate", "Associate"),
    (r"\b(certificate|cert)\b", "certificate", "Certificate"),
]

# ── Delivery format ──────────────────────────────────────────────────────────
_FORMAT_PATTERNS: list[tuple[str, str, str]] = [
    (r"\b(online|remote|distance[\s-]?learning)\b", "online", "Online"),
    (r"\b(hybrid|blended)\b", "hybrid", "Hybrid"),
    (r"\b(in[\s-]?person|on[\s-]?campus|on[\s-]?site)\b", "in_person", "In-person"),
]

# ── Major (known fields + common abbreviations); longest match wins ──────────
_MAJORS: list[tuple[str, str]] = [
    ("computer science", "Computer Science"),
    ("data science", "Data Science"),
    ("public policy", "Public Policy"),
    ("public health", "Public Health"),
    ("social work", "Social Work"),
    ("business administration", "Business Administration"),
    ("electrical engineering", "Electrical Engineering"),
    ("mechanical engineering", "Mechanical Engineering"),
    ("civil engineering", "Civil Engineering"),
    ("biomedical engineering", "Biomedical Engineering"),
    ("computer engineering", "Computer Engineering"),
    ("engineering", "Engineering"),
    ("nursing", "Nursing"),
    ("medicine", "Medicine"),
    ("psychology", "Psychology"),
    ("economics", "Economics"),
    ("finance", "Finance"),
    ("accounting", "Accounting"),
    ("marketing", "Marketing"),
    ("business", "Business"),
    ("biology", "Biology"),
    ("chemistry", "Chemistry"),
    ("physics", "Physics"),
    ("mathematics", "Mathematics"),
    ("statistics", "Statistics"),
    ("education", "Education"),
    ("architecture", "Architecture"),
    ("law", "Law"),
    ("design", "Design"),
    ("economics", "Economics"),
    ("political science", "Political Science"),
    ("international relations", "International Relations"),
    ("journalism", "Journalism"),
    ("communications", "Communications"),
]
# Abbreviations resolved as whole tokens.
_MAJOR_ABBREV: dict[str, tuple[str, str]] = {
    "cs": ("computer science", "Computer Science"),
    "ds": ("data science", "Data Science"),
    "ee": ("electrical engineering", "Electrical Engineering"),
    "ai": ("artificial intelligence", "Artificial Intelligence"),
    "ml": ("machine learning", "Machine Learning"),
}

# ── Selectivity ──────────────────────────────────────────────────────────────
_SELECTIVITY_PATTERNS: list[tuple[str, str, str]] = [
    (r"\b(highly|very|extremely)\s+selective\b", "very_high", "Highly selective"),
    (r"\b(elite|ivy|top[\s-]?tier|prestigious)\b", "very_high", "Highly selective"),
    (r"\b(selective|competitive)\b", "high", "Selective"),
    (r"\b(moderately\s+selective)\b", "medium", "Moderately selective"),
    (
        r"\b(less\s+selective|easy\s+to\s+get\s+in|high\s+acceptance|safety)\b",
        "low",
        "Less selective",
    ),
]

# ── Location: US states (+DC) and common countries / metros ──────────────────
_US_STATES = [
    "alabama",
    "alaska",
    "arizona",
    "arkansas",
    "california",
    "colorado",
    "connecticut",
    "delaware",
    "florida",
    "georgia",
    "hawaii",
    "idaho",
    "illinois",
    "indiana",
    "iowa",
    "kansas",
    "kentucky",
    "louisiana",
    "maine",
    "maryland",
    "massachusetts",
    "michigan",
    "minnesota",
    "mississippi",
    "missouri",
    "montana",
    "nebraska",
    "nevada",
    "new hampshire",
    "new jersey",
    "new mexico",
    "new york",
    "north carolina",
    "north dakota",
    "ohio",
    "oklahoma",
    "oregon",
    "pennsylvania",
    "rhode island",
    "south carolina",
    "south dakota",
    "tennessee",
    "texas",
    "utah",
    "vermont",
    "virginia",
    "washington",
    "west virginia",
    "wisconsin",
    "wyoming",
    "washington dc",
    "district of columbia",
]
_COUNTRIES = [
    "united states",
    "usa",
    "united kingdom",
    "uk",
    "canada",
    "australia",
    "germany",
    "france",
    "netherlands",
    "switzerland",
    "sweden",
    "ireland",
    "singapore",
    "japan",
    "south korea",
    "china",
    "hong kong",
    "india",
    "new zealand",
    "spain",
    "italy",
    "denmark",
    "norway",
    "finland",
    "austria",
    "belgium",
    "portugal",
]
_METROS = [
    "new york city",
    "san francisco",
    "los angeles",
    "boston",
    "chicago",
    "seattle",
    "austin",
    "london",
    "toronto",
    "vancouver",
    "berlin",
    "amsterdam",
    "singapore",
]
# Longest names first so "new york city" beats "new york".
_LOCATIONS: list[str] = sorted({*_US_STATES, *_COUNTRIES, *_METROS}, key=len, reverse=True)
_LOCATION_DISPLAY = {
    "usa": "United States",
    "uk": "United Kingdom",
    "washington dc": "Washington, DC",
    "district of columbia": "Washington, DC",
}

_SEASON_RE = re.compile(r"\b(fall|spring|summer|winter|autumn)\s+(20\d{2})\b", re.I)
_START_YEAR_RE = re.compile(
    r"\b(?:start(?:ing)?|begin(?:ning)?|enroll(?:ing)?)\s+(?:in\s+)?(20\d{2})\b", re.I
)


def _money_to_int(num: str, k: str | None) -> int:
    n = int(num.replace(",", ""))
    if k:
        n *= 1000
    return n


def _parse_budget(q: str) -> tuple[int | None, int | None]:
    """Return (min, max) annual tuition in whole dollars, or (None, None)."""
    amt = r"\$?\s?(\d[\d,]*)\s?([kK])?"
    # Range: "$20k-$50k", "20000 to 50000", "between 20k and 50k"
    rng = re.search(rf"{amt}\s*(?:-|–|to|and)\s*{amt}", q)
    if rng:
        lo = _money_to_int(rng.group(1), rng.group(2))
        hi = _money_to_int(rng.group(3), rng.group(4))
        return (min(lo, hi), max(lo, hi))
    # Upper bound: under/below/less than/max/cheaper than $X (or bare "$X")
    upper = re.search(rf"(?:under|below|less\s+than|cheaper\s+than|max|up\s+to|<=?)\s*{amt}", q)
    if upper:
        return (None, _money_to_int(upper.group(1), upper.group(2)))
    # Lower bound: over/above/at least/more than
    lower = re.search(rf"(?:over|above|at\s+least|more\s+than|>=?)\s*{amt}", q)
    if lower:
        return (_money_to_int(lower.group(1), lower.group(2)), None)
    # A bare dollar amount is treated as a ceiling (spec example "$50k").
    bare = re.search(
        rf"(?:budget\s+(?:of\s+)?)?\${amt}|{amt}\s*(?:budget|/yr|per\s+year|tuition)", q
    )
    if bare:
        g = bare.groups()
        # find the first non-None (num, k) pair
        pairs = [(g[i], g[i + 1]) for i in range(0, len(g), 2) if g[i]]
        if pairs:
            return (None, _money_to_int(pairs[0][0], pairs[0][1]))
    return (None, None)


def _budget_display(lo: int | None, hi: int | None) -> str:
    def fmt(n: int) -> str:
        return f"${n // 1000}k" if n >= 1000 and n % 1000 == 0 else f"${n:,}"

    if lo is not None and hi is not None:
        return f"{fmt(lo)}–{fmt(hi)}/yr"
    if hi is not None:
        return f"≤ {fmt(hi)}/yr"
    if lo is not None:
        return f"≥ {fmt(lo)}/yr"
    return "Budget"


def _parse_duration(q: str) -> tuple[int | None, int | None]:
    """Return (min, max) months, or (None, None)."""

    def to_months(num: int, unit: str) -> int:
        return num * 12 if unit.startswith(("year", "yr")) else num

    rng = re.search(r"(\d+)\s*(?:-|–|to)\s*(\d+)\s*(years?|yrs?|months?|mos?)", q)
    if rng:
        unit = rng.group(3)
        lo, hi = to_months(int(rng.group(1)), unit), to_months(int(rng.group(2)), unit)
        return (min(lo, hi), max(lo, hi))
    upper = re.search(
        r"(?:under|less\s+than|within|up\s+to|max)\s*(\d+)\s*(years?|yrs?|months?|mos?)", q
    )
    if upper:
        return (None, to_months(int(upper.group(1)), upper.group(2)))
    one = re.search(r"\b(\d+)[\s-]*(year|yr|month|mo)s?\b", q)
    if one:
        m = to_months(int(one.group(1)), one.group(2))
        return (m, m)
    return (None, None)


def _duration_display(lo: int | None, hi: int | None) -> str:
    def fmt(m: int) -> str:
        return f"{m // 12} yr" if m % 12 == 0 else f"{m} mo"

    if lo is not None and hi is not None and lo != hi:
        return f"{fmt(lo)}–{fmt(hi)}"
    if hi is not None:
        return f"≤ {fmt(hi)}"
    if lo is not None:
        return fmt(lo)
    return "Duration"


def parse_query(query: str) -> list[ConstraintChip]:
    """Deterministically parse a query into constraint chips. Order roughly
    follows how the chip strip reads: degree · major · location · budget ·
    format · duration · selectivity · start_term."""
    q = (query or "").strip()
    if not q:
        return []
    low = q.lower()
    chips: list[ConstraintChip] = []

    def add(category: ConstraintCategory, value: str, display: str, confidence: int) -> None:
        chips.append(
            ConstraintChip(
                category=category, value=value, display=display, confidence=confidence
            ).with_id()
        )

    # Degree (one).
    for pat, value, display in _DEGREE_PATTERNS:
        if re.search(pat, low):
            add(ConstraintCategory.degree_level, value, display, 88)
            break

    # Major (one — known phrase first, then abbreviation token).
    major_added = False
    for phrase, display in _MAJORS:
        if re.search(rf"\b{re.escape(phrase)}\b", low):
            add(ConstraintCategory.major, phrase, display, 90)
            major_added = True
            break
    if not major_added:
        for tok in re.findall(r"\b[a-z]{2,3}\b", low):
            if tok in _MAJOR_ABBREV:
                value, display = _MAJOR_ABBREV[tok]
                add(ConstraintCategory.major, value, display, 78)
                break

    # Location (one — longest match).
    for name in _LOCATIONS:
        if re.search(rf"\b{re.escape(name)}\b", low):
            display = _LOCATION_DISPLAY.get(name, name.title())
            add(ConstraintCategory.location, display, display, 85)
            break

    # Budget.
    lo, hi = _parse_budget(low)
    if lo is not None or hi is not None:
        if lo is not None and hi is not None:
            value = f"{lo}-{hi}"
        elif hi is not None:
            value = f"<={hi}"
        else:
            value = f">={lo}"
        # "affordable"/"cheap" with no number → low-confidence ceiling.
        conf = 88 if re.search(r"\d", low) else 55
        add(ConstraintCategory.budget, value, _budget_display(lo, hi), conf)
    elif re.search(r"\b(affordable|cheap|low[\s-]?cost|inexpensive)\b", low):
        add(ConstraintCategory.budget, "<=30000", "Affordable", 50)

    # Format (one).
    for pat, value, display in _FORMAT_PATTERNS:
        if re.search(pat, low):
            add(ConstraintCategory.format, value, display, 88)
            break

    # Duration.
    dlo, dhi = _parse_duration(low)
    if dlo is not None or dhi is not None:
        if dlo is not None and dhi is not None and dlo != dhi:
            value = f"{dlo}-{dhi}"
        elif dhi is not None:
            value = f"<={dhi}"
        else:
            value = f">={dlo}"
        add(ConstraintCategory.duration, value, _duration_display(dlo, dhi), 80)

    # Selectivity (one).
    for pat, value, display in _SELECTIVITY_PATTERNS:
        if re.search(pat, low):
            add(ConstraintCategory.selectivity, value, display, 75)
            break

    # Start term.
    season = _SEASON_RE.search(q)
    if season:
        value = f"{season.group(1).lower()} {season.group(2)}"
        add(ConstraintCategory.start_term, value, value.title(), 85)
    else:
        yr = _START_YEAR_RE.search(q)
        if yr:
            add(ConstraintCategory.start_term, yr.group(1), f"Starting {yr.group(1)}", 75)

    return chips


def interpretation_text(chips: list[ConstraintChip]) -> str:
    """A short human summary sentence for the chip region / low-confidence prompt."""
    if not chips:
        return "Showing all programs. Add a constraint to narrow your search."
    parts = [c.display for c in chips]
    return "Searching for programs: " + " · ".join(parts) + "."
