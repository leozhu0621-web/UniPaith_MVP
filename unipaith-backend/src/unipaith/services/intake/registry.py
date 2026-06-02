"""Spec 44 — pure signal schema registry (no DB, no I/O).

The single place that declares *which* canonical Prompt-Library signals the
engine manages and *how* each is normalized (§3.1), validated (§3.2), scored
for confidence (§5), and reconciled across sources (§7). Both the engine
service and the tests import from here.

Scope: the §6.1 match-ready required set plus a representative spread across
categories for apply-ready and completeness. Not every one of Spec 42's ~200
fields — those that already live on dedicated tables (goals/needs/identity/
prompt-library/courses…) are owned there; this registry is the canonical home
for the scalar journey-gating signals plus a generic catch-all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# ── Categories (a focused subset of Spec 42 §3) ──────────────────────────────
CATEGORIES = (
    "identity",
    "eligibility",
    "education_context",
    "academic_record",
    "tests",
    "recommendations",
    "portfolio",
    "languages",
    "intent",
    "constraints",
    "preferences",
)

# Preference-weight keys (§6.1 "at least 3 of 7 preference weights set").
PREFERENCE_WEIGHT_KEYS = (
    "cost",
    "location",
    "prestige",
    "outcomes",
    "culture",
    "flexibility",
    "support",
)


@dataclass(frozen=True)
class Signal:
    """Declarative schema for one canonical signal."""

    name: str
    category: str
    value_type: str  # str | int | enum | date | range | list | bool | dict
    label: str
    required_for_match: bool = False
    enum_values: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None
    # A free-text answer can populate this signal (the LLM-normalize path); a
    # structured form field is the high-confidence path. Drives §5 confidence.
    free_text_capable: bool = False


def _s(name: str, category: str, value_type: str, label: str, **kw: object) -> Signal:
    return Signal(name=name, category=category, value_type=value_type, label=label, **kw)  # type: ignore[arg-type]


# ── The registry ─────────────────────────────────────────────────────────────
# Order is display order within a category.
SIGNALS: dict[str, Signal] = {
    s.name: s
    for s in (
        # Identity (§3.1) — match-required core.
        _s("legal_name", "identity", "str", "Legal name", required_for_match=True),
        _s("primary_email", "identity", "str", "Email", required_for_match=True),
        _s("primary_phone", "identity", "str", "Phone"),
        _s(
            "nationality",
            "identity",
            "str",
            "Nationality",
            required_for_match=True,
            free_text_capable=True,
        ),
        _s(
            "country_of_residence",
            "identity",
            "str",
            "Country of residence",
            required_for_match=True,
            free_text_capable=True,
        ),
        # Eligibility / gating flags (§3.2 / §6.1 derived).
        _s(
            "visa_required_for_target_country_flag",
            "eligibility",
            "bool",
            "Visa likely required",
        ),
        _s(
            "has_portfolio_requirement_flag",
            "eligibility",
            "bool",
            "Portfolio likely required",
        ),
        # Education context (§3.4) — match-required.
        _s(
            "current_academic_year_level",
            "education_context",
            "enum",
            "Current level",
            required_for_match=True,
            free_text_capable=True,
            enum_values=(
                "high_school",
                "undergraduate",
                "graduate",
                "gap_year",
                "working_professional",
            ),
        ),
        _s(
            "expected_graduation_date",
            "education_context",
            "date",
            "Expected graduation",
            required_for_match=True,
            free_text_capable=True,
        ),
        _s(
            "current_institution_name",
            "education_context",
            "str",
            "Current school",
            free_text_capable=True,
        ),
        # Academic record (§3.5) — match-required (gpa OR equivalent).
        _s(
            "gpa_reported",
            "academic_record",
            "str",
            "GPA",
            required_for_match=True,
            free_text_capable=True,
        ),
        # Tests (§3.6) — apply-ready.
        _s("test_scores_provided", "tests", "bool", "Test scores on file"),
        # Recommendations (§3.7) — apply-ready.
        _s("recommenders_count", "recommendations", "int", "Recommenders", minimum=0, maximum=10),
        # Portfolio (§3.10) — apply-ready.
        _s("portfolio_pieces_count", "portfolio", "int", "Portfolio pieces", minimum=0, maximum=50),
        # Languages (§3.11).
        _s("languages_spoken", "languages", "list", "Languages"),
        # Intent (§3.12) — match-required.
        _s(
            "target_degree_level",
            "intent",
            "enum",
            "Target degree",
            required_for_match=True,
            free_text_capable=True,
            enum_values=("certificate", "associate", "bachelor", "master", "mba", "phd"),
        ),
        _s(
            "target_major_field_primary",
            "intent",
            "str",
            "Target field",
            required_for_match=True,
            free_text_capable=True,
        ),
        _s(
            "target_major_field_secondary",
            "intent",
            "str",
            "Secondary field",
            free_text_capable=True,
        ),
        _s(
            "target_start_term_season",
            "intent",
            "enum",
            "Start season",
            required_for_match=True,
            free_text_capable=True,
            enum_values=("fall", "spring", "summer", "winter"),
        ),
        _s(
            "target_start_term_year",
            "intent",
            "int",
            "Start year",
            required_for_match=True,
            free_text_capable=True,
            minimum=2024,
            maximum=2032,
        ),
        # Constraints (§3.13) — match-required.
        _s(
            "budget_band_annual_total",
            "constraints",
            "range",
            "Annual budget",
            required_for_match=True,
            free_text_capable=True,
            enum_values=("0-20k", "20-40k", "40-60k", "60-80k", "80k+"),
        ),
        _s(
            "preferred_modality",
            "constraints",
            "enum",
            "Modality",
            required_for_match=True,
            free_text_capable=True,
            enum_values=("in_person", "online", "hybrid", "no_preference"),
        ),
        _s(
            "willingness_to_relocate",
            "constraints",
            "enum",
            "Relocate?",
            free_text_capable=True,
            enum_values=("yes", "no", "conditional"),
        ),
        _s(
            "funding_need",
            "constraints",
            "enum",
            "Funding need",
            free_text_capable=True,
            enum_values=("none", "partial", "full"),
        ),
        # Preferences (§3.14) — geography + priority weights.
        _s("preferred_countries", "preferences", "list", "Preferred countries"),
        _s("preference_weights", "preferences", "dict", "Priority weights"),
    )
}

# Signals consumed by the match-ready gate as scalar requirements (§6.1).
MATCH_REQUIRED_SIGNALS = tuple(n for n, s in SIGNALS.items() if s.required_for_match)

CATEGORY_OF = {n: s.category for n, s in SIGNALS.items()}


# ── §5 confidence rules ──────────────────────────────────────────────────────
def confidence_for(
    source: str,
    *,
    structured: bool = True,
    parse_ok: bool = True,
    llm_confidence: int | None = None,
) -> int:
    """Return the §5 confidence for a value given its source + context.

    ``structured`` distinguishes a form field (95) from free text (70) for
    ``student-typed``. ``parse_ok`` distinguishes a clean doc parse (80) from a
    partial one (40). ``llm_confidence`` is the model's self-report for
    ``system-extracted`` (capped at 85).
    """
    if source == "student-typed":
        return 95 if structured else 70
    if source == "student-uploaded":
        return 80 if parse_ok else 40
    if source == "student-link":
        return 75
    if source == "system-derived":
        return 90
    if source == "system-extracted":
        base = 60 if llm_confidence is None else int(llm_confidence)
        return max(0, min(85, base))
    if source == "third-party-verified":
        return 99
    if source == "institution-supplied":
        return 95
    if source == "student-derived":
        return 70
    return 50


CONFIDENCE_CLARIFY_THRESHOLD = 60  # §5 / §6: values below this open a clarification.


# ── §7 reconciliation (source priority; higher wins, ties → latest) ──────────
SOURCE_PRIORITY: dict[str, int] = {
    "third-party-verified": 100,
    "institution-supplied": 90,
    "student-typed": 80,  # a confirmed clarification re-writes as student-typed @95
    "student-uploaded": 60,
    "student-link": 50,
    "student-derived": 40,
    "system-extracted": 30,
    "system-derived": 20,
}


def incoming_wins(new_source: str, existing_source: str) -> bool:
    """§7 — does the incoming source out-rank (or tie) the stored one?

    Ties resolve to the incoming write ("two student-typed updates → latest").
    """
    return SOURCE_PRIORITY.get(new_source, 0) >= SOURCE_PRIORITY.get(existing_source, 0)


# ── §3.1 normalize (deterministic) ───────────────────────────────────────────
_ENUM_ALIASES: dict[str, dict[str, str]] = {
    "target_degree_level": {
        "masters": "master",
        "master's": "master",
        "ms": "master",
        "ma": "master",
        "bachelors": "bachelor",
        "bachelor's": "bachelor",
        "bs": "bachelor",
        "ba": "bachelor",
        "undergraduate": "bachelor",
        "doctorate": "phd",
        "doctoral": "phd",
        "ph.d": "phd",
        "ph.d.": "phd",
    },
    "preferred_modality": {
        "in person": "in_person",
        "on campus": "in_person",
        "on-campus": "in_person",
        "remote": "online",
        "distance": "online",
        "blended": "hybrid",
        "any": "no_preference",
        "no preference": "no_preference",
    },
    "current_academic_year_level": {
        "hs": "high_school",
        "high school": "high_school",
        "secondary": "high_school",
        "undergrad": "undergraduate",
        "college": "undergraduate",
        "grad": "graduate",
        "postgraduate": "graduate",
        "working": "working_professional",
        "professional": "working_professional",
    },
}

_BUDGET_BANDS = ("0-20k", "20-40k", "40-60k", "60-80k", "80k+")


class NormalizeError(ValueError):
    """Raised when a raw value cannot be coerced to the signal's type."""


def _norm_enum(signal: Signal, raw: object) -> str:
    s = str(raw).strip().lower().replace("_", " ").strip()
    canon = s.replace(" ", "_")
    if canon in signal.enum_values:
        return canon
    alias = _ENUM_ALIASES.get(signal.name, {})
    if s in alias:
        return alias[s]
    if canon in alias:
        return alias[canon]
    # last resort — substring match against an enum value
    for ev in signal.enum_values:
        if ev.replace("_", " ") in s or s in ev.replace("_", " "):
            return ev
    raise NormalizeError(f"{signal.name}: '{raw}' is not one of {signal.enum_values}")


def _norm_budget(raw: object) -> str:
    s = str(raw).strip().lower()
    if s in _BUDGET_BANDS:
        return s
    # "around 40 grand" / "$45,000" / "40k" → band
    digits = "".join(c for c in s if c.isdigit())
    if digits:
        n = int(digits)
        if n < 1000:  # "40k" style — treat as thousands
            n *= 1000
        if n < 20000:
            return "0-20k"
        if n < 40000:
            return "20-40k"
        if n < 60000:
            return "40-60k"
        if n < 80000:
            return "60-80k"
        return "80k+"
    raise NormalizeError(f"budget_band_annual_total: cannot parse '{raw}'")


def _norm_int(signal: Signal, raw: object) -> int:
    try:
        if isinstance(raw, bool):
            raise NormalizeError(f"{signal.name}: bool is not an int")
        n = int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        # pull leading digits for "fall 2027" → not for ints; for year keep strict-ish
        digits = "".join(c for c in str(raw) if c.isdigit())
        if not digits:
            raise NormalizeError(f"{signal.name}: cannot parse int from '{raw}'") from exc
        n = int(digits)
    return n


def _norm_date(signal: Signal, raw: object) -> str:
    """Return an ISO date string. Accepts YYYY-MM-DD, YYYY, or 'fall 2027'."""
    s = str(raw).strip()
    # full ISO
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        pass
    digits = "".join(c for c in s if c.isdigit())
    if len(digits) >= 4:
        year = int(digits[:4])
        return date(year, 6, 1).isoformat()  # mid-year placeholder
    raise NormalizeError(f"{signal.name}: cannot parse date from '{raw}'")


def _norm_bool(raw: object) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in ("true", "yes", "y", "1", "required", "t")


def normalize_value(signal_name: str, raw: object) -> object:
    """§3.1 — coerce a raw value to the signal's canonical form.

    Raises :class:`NormalizeError` on a value that can't be coerced (the caller
    lowers confidence / opens a clarification rather than persisting garbage).
    """
    signal = SIGNALS.get(signal_name)
    if signal is None:
        return raw  # unknown signal → stored as-is (generic catch-all)
    if raw is None:
        raise NormalizeError(f"{signal_name}: empty value")
    t = signal.value_type
    if t == "str":
        out = str(raw).strip()
        if not out:
            raise NormalizeError(f"{signal_name}: empty string")
        return out
    if t == "enum":
        return _norm_enum(signal, raw)
    if t == "range":
        if signal_name == "budget_band_annual_total":
            return _norm_budget(raw)
        return _norm_enum(signal, raw)
    if t == "int":
        return _norm_int(signal, raw)
    if t == "date":
        return _norm_date(signal, raw)
    if t == "bool":
        return _norm_bool(raw)
    if t == "list":
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
        return [p.strip() for p in str(raw).split(",") if p.strip()]
    if t == "dict":
        return raw if isinstance(raw, dict) else {}
    return raw


# ── §3.2 validate (schema check — authoritative) ─────────────────────────────
def validate_value(signal_name: str, normalized: object) -> tuple[bool, str | None]:
    """§3.2 — type / enum / range check on a normalized value.

    Returns ``(ok, reason)``. The schema check is authoritative; an LLM check is
    advisory and feeds confidence (handled in the service).
    """
    signal = SIGNALS.get(signal_name)
    if signal is None:
        return True, None  # generic catch-all is unconstrained
    t = signal.value_type
    if t in ("enum", "range"):
        if normalized not in signal.enum_values:
            return False, f"not in {signal.enum_values}"
        return True, None
    if t == "int":
        if not isinstance(normalized, int):
            return False, "not an int"
        if signal.minimum is not None and normalized < signal.minimum:
            return False, f"< {signal.minimum}"
        if signal.maximum is not None and normalized > signal.maximum:
            return False, f"> {signal.maximum}"
        return True, None
    if t == "date":
        try:
            d = date.fromisoformat(str(normalized))
        except ValueError:
            return False, "not an ISO date"
        # §3.2 range check — 1900..a bit past today.
        if d.year < 1900 or d.year > 2100:
            return False, "year out of range"
        return True, None
    if t == "bool":
        return (
            isinstance(normalized, bool),
            None if isinstance(normalized, bool) else "not a bool",
        )
    if t == "str":
        return (bool(str(normalized).strip()), None if str(normalized).strip() else "empty")
    if t == "list":
        return (
            isinstance(normalized, list),
            None if isinstance(normalized, list) else "not a list",
        )
    if t == "dict":
        return (
            isinstance(normalized, dict),
            None if isinstance(normalized, dict) else "not a dict",
        )
    return True, None


# ── completeness weighting (§4) ──────────────────────────────────────────────
# Overall completeness counts present registry signals / total. The match-ready
# floor is 35% (§6.1); the binding constraint is the required-subset coverage.
TOTAL_SIGNALS = len(SIGNALS)
MATCH_READY_PCT_FLOOR = 35


@dataclass
class Clarification:
    """A pending confirm/correct prompt (mirrors the §6 derived field)."""

    signal_name: str
    question: str
    raw_value: object = None
    suggested_value: object = None
    confidence: int = 0
    fields: dict = field(default_factory=dict)
