"""Shared helpers for building gold-standard program catalogs without CIP padding.

Used by profile repair runs to disambiguate credential levels in program names,
assign real departments, and validate catalogs before ship.
"""

from __future__ import annotations

import re
from collections import Counter

# Bare degree abbreviations that must never appear as program_name.
BARE_DEGREE_ABBREVIATIONS = frozenset({
    "BA", "BS", "MS", "MA", "PhD", "MBA", "JD", "MD", "MEng", "MFA", "MPH", "MPP",
    "EdM", "MFin", "MBAn", "BFA", "LLM", "DMD", "CAGS",
})

# Degree-type template descriptions (CIP × award-level padding signature).
_TEMPLATE_DESC_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)

_DEGREE_PREFIX: dict[str, str] = {
    "bachelors": "Bachelor's in",
    "masters": "Master's in",
    "phd": "Doctor of Philosophy in",
    "certificate": "Graduate Certificate in",
    "professional": "Professional program in",
}


def disambiguate_program_name(field_name: str, degree_type: str) -> str:
    """Turn a bare CIP field title into a credential-disambiguated program name."""
    prefix = _DEGREE_PREFIX.get(degree_type, "Program in")
    if degree_type == "professional" and field_name.lower().startswith(
        ("doctor", "juris", "master of business")
    ):
        return field_name
    return f"{prefix} {field_name}"


def program_description(
    program_name: str,
    degree_type: str,
    school: str,
    department: str,
    *,
    delivery_format: str = "on_campus",
    university_short: str = "UC San Diego",
) -> str:
    """Field-specific description — never the degree-type template."""
    role = {
        "bachelors": "an undergraduate program",
        "masters": "a graduate program",
        "phd": "a doctoral program",
        "certificate": "a graduate certificate",
        "professional": "a professional program",
    }.get(degree_type, "a degree program")
    dept_clause = ""
    if department and department != school and department != "Programs":
        dept_clause = f", offered through the {department}"
    delivery = ""
    if delivery_format == "online":
        delivery = " Delivered online."
    elif delivery_format == "hybrid":
        delivery = " Delivered in a hybrid format."
    return (
        f"{program_name} is {role} at {university_short}'s {school}{dept_clause}.{delivery}"
    )


def validate_catalog(programs: list[dict]) -> list[str]:
    """Return human-readable violations; empty list means the catalog passes."""
    errors: list[str] = []
    names = [p.get("program_name", "") for p in programs]
    name_counts = Counter(names)
    dupes = {n: c for n, c in name_counts.items() if c > 1 and n}
    if dupes:
        top = sorted(dupes.items(), key=lambda x: -x[1])[:5]
        errors.append(f"duplicate program_name ({len(dupes)} collisions): {top}")
    bare = [n for n in names if n in BARE_DEGREE_ABBREVIATIONS]
    if bare:
        errors.append(f"bare abbreviation program_name ({len(bare)}): {bare[:5]}")
    null_dept = sum(1 for p in programs if not p.get("department"))
    if null_dept:
        errors.append(f"null/blank department on {null_dept} programs")
    programs_dept = sum(1 for p in programs if p.get("department") == "Programs")
    if programs_dept:
        errors.append(f'department=="Programs" on {programs_dept} programs')
    templ = sum(1 for p in programs if _TEMPLATE_DESC_RE.search(p.get("description", "")))
    if templ:
        errors.append(f"template descriptions on {templ} programs")
    return errors
