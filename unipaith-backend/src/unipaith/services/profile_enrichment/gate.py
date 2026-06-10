"""The verification gate — the safety core of autonomous profile enrichment.

A field value ships only when the evidence clears the gate for its sourcing
rule; otherwise it is omitted (never guessed). This module is **pure and
deterministic** — no web calls, no model calls — so the no-fabrication
guarantee is unit-testable. The LLM-judge second layer (Phase 2b) wraps this,
never replaces it.

See ``profile_standard/playbook.md`` for the per-field source rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Evidence:
    """One observed value for a field, from one source."""

    value: object
    source: str
    source_url: str
    authority: str = "weak"  # "first_party" | "authoritative" | "weak"


@dataclass(frozen=True)
class GateDecision:
    accept: bool
    value: object | None
    source: str | None
    source_url: str | None
    reason: str


def _present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        return False
    return True


def _domain(url: str) -> str:
    try:
        net = urlparse(url).netloc.lower()
        return net[4:] if net.startswith("www.") else net
    except Exception:
        return url


def _independent(evidence: list[Evidence]) -> list[Evidence]:
    """Keep one item per distinct source domain (independence proxy)."""
    seen: set[str] = set()
    out: list[Evidence] = []
    for e in evidence:
        d = _domain(e.source_url)
        if d not in seen:
            seen.add(d)
            out.append(e)
    return out


def _values_agree(values: list, *, numeric_tolerance: float = 0.05) -> bool:
    if len(values) < 2:
        return True
    first = values[0]
    if isinstance(first, (int, float)) and not isinstance(first, bool):
        nums = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(nums) != len(values):
            return False
        lo, hi = min(nums), max(nums)
        if hi == 0:
            return lo == 0
        return (hi - lo) / abs(hi) <= numeric_tolerance
    return all(v == first for v in values)


def verify(
    sourcing: str, evidence: list[Evidence], *, numeric_tolerance: float = 0.05
) -> GateDecision:
    """Decide whether a field may ship, given its sourcing rule + evidence.

    Invariant (no-fabrication): when ``accept`` is True for any *cited* sourcing
    rule, ``value`` and ``source_url`` are both non-empty.
    """
    cited = [e for e in evidence if _present(e.value) and e.source and e.source_url]

    if sourcing == "none":
        # Structural / derived — no external citation required.
        present = [e for e in evidence if _present(e.value)]
        if not present:
            return GateDecision(False, None, None, None, "no value")
        e = present[0]
        return GateDecision(True, e.value, e.source or None, e.source_url or None, "structural")

    if not cited:
        return GateDecision(False, None, None, None, "no cited evidence")

    if sourcing == "first_party":
        fp = [e for e in cited if e.authority == "first_party"]
        if not fp:
            return GateDecision(False, None, None, None, "first-party source required")
        e = fp[0]
        return GateDecision(True, e.value, e.source, e.source_url, "first-party verified")

    if sourcing == "authoritative_2x":
        strong = [e for e in cited if e.authority in ("first_party", "authoritative")]
        indep = _independent(strong)
        if len(indep) < 2:
            return GateDecision(
                False, None, None, None, "need >=2 independent authoritative sources"
            )
        if not _values_agree([e.value for e in indep], numeric_tolerance=numeric_tolerance):
            return GateDecision(False, None, None, None, "sources disagree")
        e = indep[0]
        return GateDecision(True, e.value, e.source, e.source_url, "2x authoritative agree")

    if sourcing == "official_or_curated":
        e = cited[0]
        return GateDecision(True, e.value, e.source, e.source_url, "official/curated cited")

    return GateDecision(False, None, None, None, f"unknown sourcing rule: {sourcing}")
