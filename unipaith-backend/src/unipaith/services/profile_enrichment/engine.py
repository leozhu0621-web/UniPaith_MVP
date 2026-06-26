"""Conformance-driven enrichment engine.

Given a profile snapshot, the engine asks the standard's conformance check what
is missing/stale, then for each such field gathers evidence from a ``Researcher``
and runs it through the verification gate. Accepted values go into a patch (with
their citations, which are themselves manifest fields); unverifiable fields are
omitted with a reason — never guessed.

Definition of done: a node is done only when it is **fully enriched** — every
required field present (``profile_standard.is_fully_enriched``). An omitted field
is *open work*, not done: it stays missing in the snapshot, so each subsequent run
``plan``s it again and re-attempts it (e.g. once a new authoritative source
exists). Omission keeps the no-fabrication guarantee; it does not close the field.

The engine is pure given a ``Researcher``: the live web backend (Spec 60 crawler
+ uni_knowledge) is one adapter; tests use a deterministic fixture adapter. The
LLM-judge layer (Phase 2b) wraps the deterministic gate, never replaces it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from unipaith.profile_standard import STANDARD_VERSION, check_conformance
from unipaith.profile_standard.manifest import MANIFEST, Field

from .gate import Evidence, verify


def _field_index(level: str) -> dict[str, Field]:
    """Map dotted path -> Field for a level."""
    out: dict[str, Field] = {}
    for sec in MANIFEST[level]:
        for f in sec.fields:
            out[f.path] = f
    return out


def plan(level: str, snapshot: dict, *, profile_version: int | None = None) -> list[str]:
    """Return the field paths needing enrichment.

    Missing required fields always. If the profile is stale (older standard
    version), every field is in scope so the whole profile re-conforms.
    """
    res = check_conformance(level, snapshot, profile_version=profile_version)
    if res.stale:
        return [f.path for f in _field_index(level).values()]
    return list(res.missing_fields)


class Researcher(Protocol):
    """Gathers cited evidence for one field of one target. Implemented by the
    live web adapter or a test fixture."""

    def gather(self, level: str, target: str, field: Field) -> list[Evidence]: ...


@dataclass
class EnrichmentResult:
    level: str
    target: str
    patch: dict = field(default_factory=dict)
    filled: list[str] = field(default_factory=list)
    omitted: list[dict] = field(default_factory=list)
    standard_version: int = STANDARD_VERSION

    @property
    def fully_enriched(self) -> bool:
        """Done == fully enriched: this run left nothing unfilled.

        ``omitted`` fields are NOT "done" — they are open work the routine
        re-attempts on the next run (the snapshot still shows them missing, so
        ``plan`` re-selects them). A node is done only when ``omitted`` is empty.
        """
        return not self.omitted


def _set_path(patch: dict, path: str, value) -> None:
    parts = path.split(".")
    cur = patch
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def apply_patch(snapshot: dict, patch: dict) -> dict:
    """Deep-merge a patch into a copy of the snapshot (dicts merged, leaves set)."""
    import copy

    out = copy.deepcopy(snapshot)

    def _merge(dst: dict, src: dict) -> None:
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                _merge(dst[k], v)
            else:
                dst[k] = v

    _merge(out, patch)
    return out


def enrich(
    level: str,
    target: str,
    snapshot: dict,
    researcher: Researcher,
    *,
    profile_version: int | None = None,
) -> EnrichmentResult:
    """Bring one profile toward conformance using verified evidence only."""
    index = _field_index(level)
    result = EnrichmentResult(level=level, target=target)
    for path in plan(level, snapshot, profile_version=profile_version):
        f = index.get(path)
        if f is None:
            continue
        evidence = researcher.gather(level, target, f)
        decision = verify(f.sourcing, evidence)
        if decision.accept:
            _set_path(result.patch, path, decision.value)
            result.filled.append(path)
        else:
            result.omitted.append({"path": path, "reason": decision.reason})
    # Stamp the version the profile now satisfies.
    result.patch.setdefault("_standard", {})
    result.patch["_standard"]["version"] = STANDARD_VERSION
    result.patch["_standard"]["omitted"] = [o["path"] for o in result.omitted]
    return result
