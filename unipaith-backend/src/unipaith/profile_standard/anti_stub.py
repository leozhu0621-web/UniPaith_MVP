"""Programmatic anti-stub gate for university program catalogs (enrich-profile §8.5).

``check_conformance`` is PRESENCE-only: a catalog whose every required field is
non-empty is "conformant" even when every ``description_text`` is a school-blurb /
classification / per-field stub. That hole let eight consecutive stub-swap "repair"
PRs sail through conformance + green CI and auto-merge (REPAIR_BACKLOG run 55).

This module closes the hole. It measures the description-quality tells the gold MIT
reference scores **zero** on, so a stub-swap catalog FAILS the gate instead of
passing as a "repair". Every metric below is a count of rows/fields exhibiting a
fabrication tell; a clean (gold-equal) catalog returns ``0`` for all of them.

The gate is enforced by ``tests/test_anti_stub_gate.py`` over a registry of catalogs
certified clean (``CERTIFIED_CLEAN``). A catalog ships as "repaired"/gold only by
joining that registry, at which point CI re-computes these metrics and blocks the
merge if any is non-zero. The thresholds are NOT tunable — a non-zero means the rows
are un-researched (the no-fabrication / structure-before-depth invariant), not a knob.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

# Credential designations stripped to recover the field-of-study part of a name.
# Ordered longest-first so "Master of Science in" wins over "Master of ".
_CRED_PREFIXES: tuple[str, ...] = (
    "Bachelor of Arts in ",
    "Bachelor of Science in ",
    "Bachelor of Fine Arts in ",
    "Bachelor of ",
    "Master of Science in ",
    "Master of Arts in ",
    "Master of Fine Arts in ",
    "Master of Engineering in ",
    "Master of Public Health",
    "Master of Public Policy",
    "Master of Business Administration",
    "Master of ",
    "Doctor of Philosophy in ",
    "Doctor of Medicine",
    "Doctor of Pharmacy",
    "Doctor of ",
    "PhD in ",
    "Graduate Certificate in ",
    "Certificate in ",
    "Bachelor's in ",
    "Master's in ",
    "Doctorate in ",
)

# Pure-classification descriptions: text that only states the credential level and/or
# owning unit and swaps in the field — carrying no field-specific fact (the gold
# contrast). The wording is a moving target, so this matches the durable *forms*, not
# one fixed string (REPAIR_BACKLOG miss #8). Gold MIT matches none of these.
_CLASSIFICATION_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\boffered through the [A-Z]"),  # "...offered through the Anthropology"
    re.compile(
        r"\bis (a|an) (under)?graduate (degree |major |program )?"
        r"(program |major |degree )?(offered |at |in |through )",
        re.I,
    ),
    re.compile(r"\bis a (doctoral|master's|professional|certificate) (program|degree)\b", re.I),
    re.compile(
        r" — a .+ (bachelors|masters|doctoral|professional|certificate) program offered through "
    ),
)

# Minimum shared leading body that counts as per-field stamping (miss #8 suffix-diversifier).
_SHARED_BODY_MIN_CHARS = 120
_SHARED_BODY_MIN_FRACTION = 0.5


def field_of(program_name: str) -> str:
    """The field-of-study part of a program name (credential designation stripped)."""
    for pre in _CRED_PREFIXES:
        if program_name.startswith(pre):
            rest = program_name[len(pre):].strip()
            return rest or program_name
    return program_name


def _common_prefix(a: str, b: str) -> str:
    i = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        i += 1
    return a[:i]


@dataclass(frozen=True)
class AntiStubReport:
    """Per-metric violation lists. A gold-equal catalog has every list empty."""

    n: int
    name_prefixed: list[str]        # description restates the program_name (heading doubled)
    classification: list[str]       # pure-classification / template stub descriptions
    double_period: list[str]        # ".." splice (school-blurb-into-frame breakage)
    verbatim_shared: list[str]      # description_text identical across >= 2 programs
    shared_leading_body: list[str]  # field's credential siblings share a >=120ch leading body
    cross_field_clause: list[str]   # one body stamped across rows of >= 2 DIFFERENT fields

    @property
    def violations(self) -> dict[str, list[str]]:
        return {
            "name_prefixed": self.name_prefixed,
            "classification": self.classification,
            "double_period": self.double_period,
            "verbatim_shared": self.verbatim_shared,
            "shared_leading_body": self.shared_leading_body,
            "cross_field_clause": self.cross_field_clause,
        }

    @property
    def is_clean(self) -> bool:
        return not any(self.violations.values())

    def summary(self) -> str:
        parts = [f"{k}={len(v)}" for k, v in self.violations.items() if v]
        return ", ".join(parts) if parts else "clean"


def _desc(program: dict) -> str:
    return (program.get("description") or program.get("description_text") or "").strip()


def analyze(programs: list[dict]) -> AntiStubReport:
    """Compute the gold-MIT-0% anti-stub metrics over a program catalog.

    Each program is a dict with at least ``program_name`` and ``description`` (or
    ``description_text``). Returns an :class:`AntiStubReport` whose lists are all empty
    for a clean catalog.
    """
    descs = [_desc(p) for p in programs]
    names = [p.get("program_name") or "" for p in programs]

    name_prefixed = [
        names[i] for i, d in enumerate(descs) if names[i] and d.startswith(names[i])
    ]
    classification = [
        names[i]
        for i, d in enumerate(descs)
        if d and any(rx.search(d) for rx in _CLASSIFICATION_RES)
    ]
    double_period = [names[i] for i, d in enumerate(descs) if ".." in d]

    counts: dict[str, int] = defaultdict(int)
    for d in descs:
        if d:
            counts[d] += 1
    verbatim_shared = [names[i] for i, d in enumerate(descs) if d and counts[d] > 1]

    # Per-field shared leading body across a field's credential siblings.
    by_field: dict[str, list[str]] = defaultdict(list)
    for d, n in zip(descs, names):
        by_field[field_of(n)].append(d)
    shared_leading_body: list[str] = []
    for field, ds in by_field.items():
        if len(ds) < 2:
            continue
        prefix = ds[0]
        for other in ds[1:]:
            prefix = _common_prefix(prefix, other)
        shortest = min(len(x) for x in ds)
        if (
            len(prefix) >= _SHARED_BODY_MIN_CHARS
            and shortest
            and len(prefix) >= _SHARED_BODY_MIN_FRACTION * shortest
        ):
            shared_leading_body.append(field)

    # Catalog-wide: one leading body stamped across rows of >= 2 DIFFERENT fields
    # (the school-blurb stamp the field-keyed count above never compares). The field name
    # is interpolated into the blurb ("{Univ}'s {field} program connects to {SCHOOL
    # blurb}…"), so neutralize the field token before comparing — otherwise the leading
    # text differs per row only by the swapped-in field and the stamp hides. The blurb may
    # lowercase the field token ("anthropology program connects…") while program_name is
    # title-cased ("… in Anthropology"), so the neutralization is CASE-INSENSITIVE — a
    # case-sensitive replace would miss the lowercase occurrence and let the stamp hide.
    head_to_fields: dict[str, set[str]] = defaultdict(set)
    for d, n in zip(descs, names):
        if len(d) < _SHARED_BODY_MIN_CHARS:
            continue
        field = field_of(n)
        normalized = re.sub(re.escape(field), "{FIELD}", d, flags=re.IGNORECASE) if field else d
        head_to_fields[normalized[: _SHARED_BODY_MIN_CHARS * 2]].add(field)
    cross_field_clause = [
        head for head, fields in head_to_fields.items() if len(fields) >= 2
    ]

    return AntiStubReport(
        n=len(programs),
        name_prefixed=name_prefixed,
        classification=classification,
        double_period=double_period,
        verbatim_shared=verbatim_shared,
        shared_leading_body=shared_leading_body,
        cross_field_clause=cross_field_clause,
    )
