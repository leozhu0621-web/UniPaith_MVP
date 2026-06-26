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
    )


# ── Definition of done: FULLY ENRICHED ──────────────────────────────────────
# A node is "done" only when every required field is actually present — NOT when
# the remaining gaps are merely recorded in ``_standard.omitted``. A verified-
# unavailable field is *open work* the enrichment routine re-attempts each run
# (e.g. when a new authoritative source appears), never a terminal "done" state.
# ``is_fully_enriched`` is the single, importable bar the skills/routine/loop and
# reporting follow. (``check_conformance(...).conformant`` is the same presence-
# only test; this name makes the intent explicit and is the canonical entry point.)


@dataclass
class CompletenessResult:
    """Strict, presence-only enrichment completeness for one node.

    Unlike the test-time acceptance, this NEVER credits ``_standard.omitted`` as
    done: ``required_total`` counts every required, enrich-owned field, and
    ``present`` is how many are actually filled. ``remaining`` is the work left to
    reach *fully enriched* (it includes fields currently recorded as omitted).
    """

    level: str
    fully_enriched: bool
    required_total: int
    present: int
    remaining: list[str] = field(default_factory=list)
    stale: bool = False

    @property
    def pct(self) -> int:
        if self.required_total == 0:
            return 100
        return round(100 * self.present / self.required_total)


def enrichment_completeness(
    level: str, snapshot: dict, *, profile_version: int | None = None
) -> CompletenessResult:
    """How close a node is to *fully enriched* (every required field present).

    The omitted-with-reason shortcut does not count toward done here — that is the
    whole point of the "fully enriched = done" rule. Use this for routine targets,
    the self-driving loop's done check, and any completeness reporting.
    """
    sections: list[Section] = MANIFEST[level]
    required: list[str] = []
    remaining: list[str] = []
    for sec in sections:
        if not sec.required:
            continue
        for f in sec.fields:
            if not (f.enrich and f.required):
                continue
            required.append(f.path)
            if not _present(_resolve(snapshot, f.path)):
                remaining.append(f.path)
    stale = profile_version is not None and profile_version < STANDARD_VERSION
    present = len(required) - len(remaining)
    return CompletenessResult(
        level=level,
        fully_enriched=(not remaining and not stale),
        required_total=len(required),
        present=present,
        remaining=remaining,
        stale=stale,
    )


def is_fully_enriched(level: str, snapshot: dict, *, profile_version: int | None = None) -> bool:
    """The completion bar: every required field present and the node not stale.

    This is the definition of *done* the routine follows — a node whose only gaps
    are recorded in ``_standard.omitted`` is NOT done; it is still open work.
    """
    return enrichment_completeness(level, snapshot, profile_version=profile_version).fully_enriched
