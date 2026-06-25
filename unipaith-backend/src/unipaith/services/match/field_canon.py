"""Deterministic field-of-study canonicalizer (Spec 3 §3 — field categorical).

The CPEF ``field`` signal compares a student's ``field_of_study`` against a
program's ``fields_offered`` via ``fit_categorical_best`` + ``FIELD_SIM_TABLE``.
That comparison is an exact ``==`` (or a sim-table lookup) over *lower_snake
canonical* field tokens — but the underlying ORM stores neither side in that
shape:

- ``AcademicRecord.field_of_study`` is free text (``"Data Science"``, ``"CS"``,
  ``"Computer Science & Engineering"``).
- ``Program`` has no field column at all — only ``cip_code`` (a CIP code) and
  ``program_name`` free text.

Without a shared canonical token the field signal can never fire on live data
(the strings never ``==``). This module is the single deterministic, fail-soft
projection both sides run through so they speak the SAME vocabulary — the exact
token set of ``FIELD_SIM_TABLE``.

It invents nothing: it normalizes / looks up text that genuinely exists. A field
it cannot confidently classify returns ``None`` (the caller then emits no field
token, so an unclassifiable field injects no phantom signal — gated, per spec).
"""

from __future__ import annotations

import re

# The canonical field vocabulary the matcher reasons over — the union of every
# token appearing in ``FIELD_SIM_TABLE``. Kept here as the single source so a
# new sim-table entry and a new canonical token stay in lockstep.
CANONICAL_FIELDS: frozenset[str] = frozenset(
    {
        "data_science",
        "statistics",
        "computer_science",
        "mathematics",
        "economics",
        "engineering",
        "physics",
        "biology",
        "neuroscience",
        "public_health",
        "chemistry",
        "psychology",
        "business",
        "finance",
        "political_science",
        "history",
        "art_history",
        "english",
    }
)

# Free-text alias → canonical token. Lowercased, punctuation-stripped substrings
# matched against the normalized input. ORDER MATTERS for substring matching:
# more-specific multiword aliases are checked before broader single words (e.g.
# "data science" before "science", "computer science" before "computer"), so a
# "Data Science" field is not mis-bucketed by a looser later rule. Every value is
# a member of CANONICAL_FIELDS.
_ALIASES: tuple[tuple[str, str], ...] = (
    ("data science", "data_science"),
    ("data analytics", "data_science"),
    ("machine learning", "data_science"),
    ("artificial intelligence", "computer_science"),
    ("computer science", "computer_science"),
    ("computer engineering", "computer_science"),
    ("software engineering", "computer_science"),
    ("information science", "computer_science"),
    ("public health", "public_health"),
    ("political science", "political_science"),
    ("art history", "art_history"),
    ("statistics", "statistics"),
    ("biostatistics", "statistics"),
    ("mathematics", "mathematics"),
    ("applied math", "mathematics"),
    ("economics", "economics"),
    ("neuroscience", "neuroscience"),
    ("psychology", "psychology"),
    ("finance", "finance"),
    ("accounting", "finance"),
    ("business", "business"),
    ("management", "business"),
    ("chemistry", "chemistry"),
    ("biology", "biology"),
    ("biomedical", "biology"),
    ("physics", "physics"),
    ("english", "english"),
    ("literature", "english"),
    ("history", "history"),
    ("engineering", "engineering"),
)

# CIP full 2-digit family → canonical token (the program-side fallback when the
# program_name yields no alias hit). Coarse but real: a CIP family is the most
# specific field signal a bare crawled program carries. Only families that map
# cleanly to a single canonical token are listed; an ambiguous family is omitted
# (returns None → no field token), never guessed.
_CIP_FAMILY_FIELD: dict[str, str] = {
    "11": "computer_science",  # Computer & Information Sciences
    "14": "engineering",  # Engineering
    "22": "political_science",  # Legal Professions & Studies (same head as law_policy interest)
    "26": "biology",  # Biological & Biomedical Sciences
    "27": "mathematics",  # Mathematics & Statistics
    "40": "physics",  # Physical Sciences (chemistry/physics — physics as head)
    "42": "psychology",  # Psychology
    "45": "political_science",  # Social Sciences (poli-sci as head)
    "51": "public_health",  # Health Professions
    "52": "business",  # Business / Management / Finance
    "54": "history",  # History
}


def _normalize(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace — so "C.S." and
    "Computer-Science" normalize alike before alias matching."""
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def canonical_field(text: str | None) -> str | None:
    """Map a free-text field / major name to a canonical token, or None.

    Exact canonical token passes through; otherwise the first alias whose phrase
    appears in the normalized text wins; an unclassifiable name returns None.
    """
    if not text:
        return None
    norm = _normalize(text)
    if not norm:
        return None
    # Exact canonical token already (e.g. an upstream already-canonical value).
    snake = norm.replace(" ", "_")
    if snake in CANONICAL_FIELDS:
        return snake
    for phrase, token in _ALIASES:
        if phrase in norm:
            return token
    return None


# Onboarding-wizard interest track (frontend ``INTEREST_TRACKS`` value) → canonical
# field token. The wizard's interest values (``cs_data_ai``, ``law_policy``, …) are
# product groupings, NOT free-text majors, so ``canonical_field`` can't parse them —
# this is their explicit bridge into the matcher's field vocabulary so a student who
# only completed signup+onboarding (never Discovery) still gets a field signal + the
# wrong-discipline veto (todo 1.1 / 3.2). CONSERVATIVE: only tracks that map cleanly
# to a single canonical token are listed; a broad/ambiguous track (arts, performing
# arts, humanities, education, journalism, languages, environment) is intentionally
# OMITTED → no field token → the field signal stays permissive for it (never a
# phantom veto). Keep the keys in lockstep with frontend ``onboarding/catalog.ts``.
INTEREST_TRACK_FIELD: dict[str, str] = {
    "cs_data_ai": "computer_science",
    "comp_engineering_robotics": "computer_science",
    "engineering": "engineering",
    "business": "business",
    "entrepreneurship_product": "business",
    "health": "public_health",
    "math_physics_chemistry_sciences": "mathematics",
    "law_policy": "political_science",
}


def interest_track_to_field(track: str | None) -> str | None:
    """Map an onboarding interest-track value to a canonical field token, or None.

    Fail-soft: an unknown/ambiguous track returns None (the caller then emits no
    field token, so it injects no phantom field signal), matching ``canonical_field``.
    """
    if not track:
        return None
    return INTEREST_TRACK_FIELD.get(str(track).strip().lower())


def fields_offered_for_program(
    *, cip_code: str | None = None, program_name: str = "", field_of_study: str | None = None
) -> list[str]:
    """Derive a program's canonical offered-field list from REAL attributes.

    Precedence: an explicit field_of_study (rare on Program), then a
    program_name alias hit, then the CIP 2-digit family. Returns ``[]`` (no field
    token → no field signal) when none classify — never a guessed field.
    """
    for candidate in (field_of_study, program_name):
        token = canonical_field(candidate)
        if token is not None:
            return [token]
    fam = re.match(r"(\d{2})", str(cip_code).strip()) if cip_code else None
    if fam is not None:
        token = _CIP_FAMILY_FIELD.get(fam.group(1))
        if token is not None:
            return [token]
    return []
