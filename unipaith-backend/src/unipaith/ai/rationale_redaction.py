"""Spec 06 §3 / §5.5 / §7 — asymmetric match-rationale projection.

The A5 rationale agent (`ai/rationale.py`) produces ONE grounded artifact
per (student, program): three prose paragraphs plus field-level citations
(`cited_student_fields`, `cited_program_fields`) and the score breakdowns.

Spec 06's "key insight" (§3) is that this single artifact is served
**asymmetrically**:

  * **Institution reviewers** get the FULL, evidence-linked view — every
    citation and every comparative/internal matching signal. This is the
    reviewer's audit trail (spec 32 §2 / §6).
  * **Students** get a REDACTED, safe view — the human-readable prose plus
    citations to their OWN profile signals, but WITHOUT the sensitive
    comparative signals (cohort percentiles, selectivity deltas, seat
    scarcity, confidence-calibration internals, raw fitness weights).

This module is the single source of truth for that redaction map. Both the
student rationale endpoints and the institution rationale endpoint route
through `project_for_student` / `project_for_institution`, so the asymmetry
can never drift between the two surfaces.

Invariant (enforced by `tests/test_rationale_redaction.py`): the student
projection — fully flattened — contains NONE of the institution-only signal
keys; the institution projection is loss-less.

Spec 06 §7 action item ("define a redaction map — which matching signals are
institution-only") is realized here, and documented in specs 11 + 32.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── The redaction map ───────────────────────────────────────────────────────
#
# Case-insensitive substrings that mark a breakdown key OR a citation path
# segment as a *sensitive comparative / internal* matching signal. These are
# visible to institution reviewers but redacted from students. Substring match
# (not exact) so derived keys like ``selectivity_delta`` or
# ``cohort_percentile_band`` are caught without enumerating every variant.
INSTITUTION_ONLY_KEY_SUBSTRINGS: tuple[str, ...] = (
    # confidence-calibration internals — model plumbing, not student-facing
    "calibrat",  # calibration, calibrator_fitted, calibrator_n_samples
    "raw_weight",
    "weight_vector",
    "model_internal",
    # cohort / peer comparison — how this applicant ranks vs others
    "cohort",
    "percentile",
    "peer",
    "rank_vs",
    "ranking_vs",
    "comparison",
    "comparative",
    "relative_to",
    "applicant_pool",
    "pool_position",
    # institution-competitiveness / scarcity signals
    "selectivity",
    "admit_rate",
    "acceptance_rate",
    "yield",
    "seat",
    "capacity",
    "scarcity",
    "competitiveness",
    "demand",
    # fairness / integrity internals (institution + audit only)
    "disparate",
    "fairness_flag",
    "integrity_internal",
)


def is_institution_only(key: str) -> bool:
    """True when a breakdown key or citation-path segment names a sensitive
    comparative/internal signal that students must not see."""
    if not key:
        return False
    low = str(key).lower()
    return any(sub in low for sub in INSTITUTION_ONLY_KEY_SUBSTRINGS)


def redact_mapping(value: Any) -> Any:
    """Recursively drop institution-only keys from a breakdown mapping.

    Lists are walked element-wise; scalars pass through. The returned object
    is a fresh structure (never mutates the input) so the institution
    projection of the same row stays intact.
    """
    if isinstance(value, dict):
        return {k: redact_mapping(v) for k, v in value.items() if not is_institution_only(str(k))}
    if isinstance(value, list):
        return [redact_mapping(v) for v in value]
    return value


def redact_citations(paths: list[str] | None) -> list[str]:
    """Drop citation paths that touch an institution-only signal.

    A path like ``sparse.cohort_percentile`` or ``program.selectivity_delta``
    is removed; a path like ``sparse.research_experience`` (the student's own
    data) or ``program.outcomes`` (a public program fact) is kept. Match is
    per dot-segment so a sensitive segment anywhere in the path redacts it.
    """
    out: list[str] = []
    for path in paths or []:
        segments = str(path).split(".")
        if any(is_institution_only(seg) for seg in segments):
            continue
        out.append(path)
    return out


# ── Projections ─────────────────────────────────────────────────────────────


@dataclass
class RationaleProjection:
    """One audience-specific view of a match rationale.

    `audience` is ``"student"`` (redacted/safe) or ``"institution"`` (full
    evidence-linked). `redacted` is True when any signal was withheld for this
    audience — surfaced to the UI so the student view can omit an "evidence"
    affordance and the institution view can badge itself as the full record.
    """

    audience: str
    rationale_text: str = ""
    cited_student_fields: list[str] = field(default_factory=list)
    cited_program_fields: list[str] = field(default_factory=list)
    fitness_breakdown: dict[str, Any] = field(default_factory=dict)
    confidence_breakdown: dict[str, Any] = field(default_factory=dict)
    redacted: bool = False
    grounded: bool = True


def project_for_institution(
    *,
    rationale_text: str,
    cited_student_fields: list[str] | None,
    cited_program_fields: list[str] | None,
    fitness_breakdown: dict[str, Any] | None = None,
    confidence_breakdown: dict[str, Any] | None = None,
    grounded: bool = True,
) -> RationaleProjection:
    """The full, loss-less reviewer view (spec 32 §2 / §6). Nothing is
    withheld — this is the institution's evidence-linked audit trail."""
    return RationaleProjection(
        audience="institution",
        rationale_text=rationale_text or "",
        cited_student_fields=list(cited_student_fields or []),
        cited_program_fields=list(cited_program_fields or []),
        fitness_breakdown=dict(fitness_breakdown or {}),
        confidence_breakdown=dict(confidence_breakdown or {}),
        redacted=False,
        grounded=grounded,
    )


def project_for_student(
    *,
    rationale_text: str,
    cited_student_fields: list[str] | None,
    cited_program_fields: list[str] | None,
    fitness_breakdown: dict[str, Any] | None = None,
    confidence_breakdown: dict[str, Any] | None = None,
    grounded: bool = True,
) -> RationaleProjection:
    """The redacted, safe student view (spec 06 §3 / §5.5).

    Keeps the plain-language prose and the student's OWN profile-signal
    citations; redacts program citations that touch sensitive comparative
    signals and strips institution-only keys from both breakdowns.
    """
    safe_program_citations = redact_citations(cited_program_fields)
    redacted_fitness = redact_mapping(fitness_breakdown or {})
    redacted_confidence = redact_mapping(confidence_breakdown or {})

    was_redacted = (
        len(safe_program_citations) != len(cited_program_fields or [])
        or redacted_fitness != (fitness_breakdown or {})
        or redacted_confidence != (confidence_breakdown or {})
    )

    return RationaleProjection(
        audience="student",
        rationale_text=rationale_text or "",
        # The student's own data reflected back is always safe.
        cited_student_fields=list(cited_student_fields or []),
        cited_program_fields=safe_program_citations,
        fitness_breakdown=redacted_fitness,
        confidence_breakdown=redacted_confidence,
        redacted=was_redacted,
        grounded=grounded,
    )


def flatten_keys(value: Any) -> set[str]:
    """All dict keys reachable in a nested structure — used by the contract
    test to assert the student projection leaks no institution-only key."""
    keys: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            keys.add(str(k))
            keys |= flatten_keys(v)
    elif isinstance(value, list):
        for v in value:
            keys |= flatten_keys(v)
    return keys
