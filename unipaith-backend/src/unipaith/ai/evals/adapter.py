"""Spec 62 §3/§5 — the consumer-agnostic eval-adapter abstraction.

The shared harness is *one service, many consumers*. Everything generic — the
runner, the gate, A/B, drift, the metrics surface — lives in the harness; each
consumer plugs in through a thin **adapter** that implements three hooks:

  - ``produce(case)``      — run the agent / extractor on a case → output.
  - ``rubric_dimensions()``— the scored dimensions (some deterministic, some
    judged) the output is graded against.
  - ``materialize(event)`` — turn a real production failure into a curated,
    versioned golden case so nothing re-breaks (§2 "grows from real failures").

This module owns the **shared shapes** so the chatbot adapter (`chatbot_adapter`)
and the extraction adapter (`extraction_adapter`) speak the same language and the
harness can run either without knowing which it is. ``EvalCase`` is a superset:
it keeps the exact field prefix the chatbot adapter already used (so existing
constructions and ``runner.py``'s lazy imports are untouched) and adds the
extraction + shared-metadata fields with defaults.

Dependency-light (dataclasses + typing only) so the transparency layer can import
it without pulling in the AI client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# ── The case shape (spec 62 §2) ─────────────────────────────────────────────
# A superset that serves both consumers. The leading fields preserve the
# original chatbot ``EvalCase`` order (id, agent, prompt, dimension, context,
# source, expect_refusal, must_not_contain) so positional/keyword constructions
# in chatbot_adapter.py and runner.py keep working verbatim; the extraction +
# shared-metadata fields are appended with defaults.


@dataclass(frozen=True)
class EvalCase:
    """One eval case = input + expected/rubric + dimensions + metadata (§2)."""

    id: str
    # ── chatbot fields (original prefix, unchanged) ──
    agent: str = "student"  # was required; defaulted so extraction cases can omit it
    prompt: str = ""
    dimension: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    source: str = "curated"  # curated | production | synthetic (§2)
    expect_refusal: bool = False
    must_not_contain: tuple[str, ...] = ()
    # ── spec-62 generalization ──
    consumer: str = "chatbot"  # which adapter owns this case
    domain: str | None = None  # extraction: the reference domain (occupations, …)
    payload: dict[str, Any] = field(default_factory=dict)  # extraction: source page
    expected: dict[str, Any] = field(default_factory=dict)  # extraction: gold fields
    severity: str = "normal"  # normal | high | critical (§2)
    version: str = "v1"  # golden-set version this case belongs to


# ── Rubric + scoring shapes ─────────────────────────────────────────────────
@dataclass(frozen=True)
class DimensionSpec:
    """One scored rubric dimension, consumer-described for the harness + surface."""

    key: str
    label: str
    hard_floor: bool
    kind: str  # "deterministic" | "judge"
    summary: str = ""


@dataclass(frozen=True)
class JudgeScore:
    """One dimension's score from the LLM judge (auditable, §4)."""

    dimension: str
    score: float
    passed: bool
    justification: str = ""


@dataclass(frozen=True)
class CaseScore:
    """The harness's per-case verdict — deterministic-first, judge-second (§4)."""

    case_id: str
    consumer: str
    deterministic_passed: bool
    dimension_scores: dict[str, float | None]  # None = deferred (judge, real-mode only)
    passed: bool
    mode: str  # "deterministic" | "real"
    cost_usd: float = 0.0
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsumerReport:
    """The aggregate gate result for one consumer's golden set (§6 CI gate)."""

    consumer: str
    version: str
    mode: str
    case_count: int
    passed_cases: int
    gate_passed: bool
    per_dimension: dict[str, dict[str, float]]  # dim → {"score": mean, "min": worst}
    hard_floor_failures: list[str]
    case_scores: list[CaseScore]

    @property
    def pass_rate(self) -> float:
        return (self.passed_cases / self.case_count) if self.case_count else 1.0


# ── The adapter contract (§3) ───────────────────────────────────────────────
@runtime_checkable
class EvalAdapter(Protocol):
    """Three hooks + a self-description. Everything else is shared (§3)."""

    consumer: str
    title: str
    spec: str
    file: str
    status: str  # "live" | "partial" | "planned"
    produce_blurb: str
    rubric_blurb: str
    materialize_blurb: str
    materialize_source: str

    def rubric_dimensions(self) -> tuple[DimensionSpec, ...]:
        """The scored dimensions (deterministic + judged) for this consumer."""
        ...

    def deterministic_checks(self) -> tuple[tuple[str, str], ...]:
        """(name, blurb) for each deterministic check run before the judge (§4)."""
        ...

    def materialize(self, event: dict[str, Any]) -> EvalCase:
        """Turn a production failure into a curated golden case (§5)."""
        ...

    async def score_case(self, case: EvalCase, *, real: bool) -> CaseScore:
        """Produce + deterministic-first + (real) judge → a per-case verdict."""
        ...


def hard_floor_keys(dims: tuple[DimensionSpec, ...]) -> tuple[str, ...]:
    return tuple(d.key for d in dims if d.hard_floor)
