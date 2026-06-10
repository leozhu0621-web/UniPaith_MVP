"""Pure conformance check: does a profile snapshot satisfy the manifest?

A *snapshot* is a plain dict of the profile's persisted shape — its columns and
JSONB blobs (e.g. ``{"outcomes_data": {...}, "cost_data": {...}, ...}`` for a
program). The check resolves each manifest field's dotted ``path`` and reports
what's missing and whether the profile is stale versus ``STANDARD_VERSION``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .manifest import MANIFEST, STANDARD_VERSION, Section


def _resolve(snapshot: dict, path: str):
    cur = snapshot
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        return False
    return True


def _omitted_paths(snapshot: dict) -> set[str]:
    """The field paths the node has legitimately recorded as verified-unavailable
    in ``_standard.omitted`` — these don't block conformance."""
    std = snapshot.get("_standard")
    if not isinstance(std, dict):
        return set()
    raw = std.get("omitted")
    if not isinstance(raw, (list, tuple)):
        return set()
    return {str(p) for p in raw}


@dataclass
class ConformanceResult:
    level: str
    conformant: bool
    missing_sections: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    stale: bool = False
    omitted: list[str] = field(default_factory=list)


def check_conformance(
    level: str, snapshot: dict, *, profile_version: int | None = None
) -> ConformanceResult:
    """Return which required sections/fields a snapshot is missing, and whether
    it is stale versus the current ``STANDARD_VERSION``."""
    sections: list[Section] = MANIFEST[level]
    missing_sections: list[str] = []
    missing_fields: list[str] = []
    omitted = _omitted_paths(snapshot)
    for sec in sections:
        sec_has_any = False
        for f in sec.fields:
            if not f.enrich:
                # Inherited from a parent profile or render-only — not this
                # profile's responsibility; documented but not required here.
                continue
            present = _present(_resolve(snapshot, f.path))
            if present:
                sec_has_any = True
            elif f.path in omitted:
                # Verified-unavailable and recorded in _standard.omitted — an
                # honest omission, so it doesn't count as a missing field and
                # satisfies the section's "has content" requirement.
                sec_has_any = True
            elif f.required and sec.required:
                missing_fields.append(f.path)
        if sec.required and not sec_has_any:
            missing_sections.append(sec.id)
    stale = profile_version is not None and profile_version < STANDARD_VERSION
    conformant = not missing_fields and not missing_sections and not stale
    return ConformanceResult(
        level=level,
        conformant=conformant,
        missing_sections=missing_sections,
        missing_fields=missing_fields,
        stale=stale,
        omitted=sorted(omitted),
    )
