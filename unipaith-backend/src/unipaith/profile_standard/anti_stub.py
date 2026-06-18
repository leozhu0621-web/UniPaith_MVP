"""Anti-stub catalog gates — every fabrication tell must read 0% (gold MIT baseline).

Used by profile modules at import time and by CI tests so stub-swap PRs cannot auto-merge.
See enrich-profile SKILL.md miss #8 / §8.5.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable

SCHOOL_BLURB_RE = re.compile(
    r"connects to .+\.\.?\s*Students build depth in",
    re.I,
)

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate|a graduate|a doctoral|a professional) (program|major) "
    r"(at|in|offered through)",
    re.I,
)


def school_blurb_violations(programs: list[dict]) -> list[str]:
    hits = [
        p.get("slug", "?")
        for p in programs
        if SCHOOL_BLURB_RE.search(p.get("description") or "")
    ]
    if hits:
        return [f"school-blurb descriptions on {len(hits)} programs (e.g. {hits[0]})"]
    return []


def name_prefix_violations(programs: list[dict]) -> list[str]:
    hits = [
        p.get("slug", "?")
        for p in programs
        if (p.get("description") or "").startswith(p.get("program_name") or "")
    ]
    if hits:
        return [f"name-prefixed descriptions on {len(hits)} programs"]
    return []


def verbatim_shared_violations(programs: list[dict]) -> list[str]:
    counts = Counter(p.get("description") for p in programs)
    shared = sum(c - 1 for c in counts.values() if c > 1)
    if shared:
        return [f"verbatim-identical descriptions shared across {shared} rows"]
    return []


def shared_body_violations(
    programs: list[dict],
    field_key_fn: Callable[[dict], str],
    *,
    min_prefix: int = 120,
    min_fraction: float = 0.5,
) -> list[str]:
    """Fail when credential siblings share a long leading body (suffix-diversifier evasion)."""
    by_field: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_field[field_key_fn(spec)].append(spec)

    errors: list[str] = []
    for field, rows in by_field.items():
        if len(rows) < 2:
            continue
        descs = [r.get("description") or "" for r in rows]
        if len(set(descs)) < len(descs):
            errors.append(f"verbatim-identical descriptions in field {field!r}")
            continue
        prefix = descs[0]
        shortest = min(len(d) for d in descs)
        for d in descs[1:]:
            i = 0
            while i < min(len(prefix), len(d)) and prefix[i] == d[i]:
                i += 1
            prefix = prefix[:i]
        if len(prefix) >= min_prefix and len(prefix) >= min_fraction * shortest:
            errors.append(
                f"shared description body prefix ({len(prefix)} chars) in field {field!r}"
            )
    return errors


def cross_field_shared_clause_violations(
    programs: list[dict],
    *,
    min_clause: int = 120,
) -> list[str]:
    """Fail when one substantive clause is stamped across ≥2 different fields."""
    clause_to_fields: dict[str, set[str]] = defaultdict(set)
    for spec in programs:
        desc = (spec.get("description") or "").strip()
        if len(desc) < min_clause:
            continue
        # Use the opening substantive clause (first sentence or min_clause chars).
        end = desc.find(". ")
        clause = desc[: end + 1 if end >= min_clause else min_clause].strip()
        if len(clause) >= min_clause:
            field = spec.get("program_name") or spec.get("slug", "")
            clause_to_fields[clause].add(field)
    errors: list[str] = []
    for clause, fields in clause_to_fields.items():
        if len(fields) >= 2:
            errors.append(
                f"cross-field shared clause ({len(clause)} chars) on {len(fields)} fields"
            )
    return errors[:5]  # cap noise — any hit is a fail


def dept_field_echo_violations(
    programs: list[dict],
    field_key_fn: Callable[[dict], str],
) -> list[str]:
    hits = sum(
        1
        for p in programs
        if p.get("department") and p.get("department") == field_key_fn(p)
    )
    if hits:
        return [f"department echoes field name on {hits}/{len(programs)} programs"]
    return []


def classification_stub_violations(programs: list[dict]) -> list[str]:
    hits = sum(
        1 for p in programs if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
    )
    if hits:
        return [f"classification stub descriptions on {hits} programs"]
    return []


def catalog_anti_stub_violations(
    programs: list[dict],
    field_key_fn: Callable[[dict], str],
) -> list[str]:
    """Run all anti-stub gates; return combined violation messages (empty = pass)."""
    violations: list[str] = []
    violations.extend(school_blurb_violations(programs))
    violations.extend(name_prefix_violations(programs))
    violations.extend(verbatim_shared_violations(programs))
    violations.extend(shared_body_violations(programs, field_key_fn))
    violations.extend(cross_field_shared_clause_violations(programs))
    violations.extend(dept_field_echo_violations(programs, field_key_fn))
    violations.extend(classification_stub_violations(programs))
    return violations
