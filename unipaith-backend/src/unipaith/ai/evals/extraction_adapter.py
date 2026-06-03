"""Spec 62 §5 · spec 60 §13B — the extraction eval adapter (consumer #2).

The shared harness proves itself the moment a *second*, very different consumer
plugs in through the same three hooks with no duplicated eval code. The crawler's
``SourceExtractionAgent`` (spec 60) is graded here on:

  - ``per_field_prf``   — precision / recall / F1 of emitted (field, value) pairs
    against a labeled golden page.
  - ``no_fabrication``  — **hard floor**: every emitted field is grounded in the
    source AND in the domain schema's allowlist (spec 60 §15). Reuses the
    extractor's own ``verify_grounded``.
  - ``schema_validity`` — no field outside ``schema_for(domain).fields``.
  - ``normalization``   — numeric fields coerced to numbers, matching the gold.

All four are **deterministic** (no model call), so this consumer gates in CI with
no API key — exactly what §4 ("deterministic checks first") + a hard floor demand.
The §4 *independent judge* (Claude grading the Qwen extraction's subjective
"is-this-the-right-value" calls) is a real-mode-only refinement; the gate below
does not need it.

Same three-hook contract as ``chatbot_adapter.ChatbotAdapter`` — that symmetry is
the whole point of spec 62.
"""

from __future__ import annotations

from typing import Any

from unipaith.ai.evals.adapter import CaseScore, DimensionSpec, EvalCase
from unipaith.services.crawler.extractor import ExtractionResult, SourceExtractionAgent
from unipaith.services.crawler.schemas import schema_for

CONSUMER = "extraction"

# Per-dimension pass thresholds (mirrors runner.THRESHOLDS for the suites).
_MIN_F1 = 0.85
_MIN_NORMALIZATION = 0.9

_DETERMINISTIC_BLURBS: dict[str, str] = {
    "no_fabrication": "Every emitted field is grounded in the source AND in the "
    "domain schema — the extractor can't invent (spec 60 §15).",
    "schema_validity": "No field outside the domain schema's writable allowlist.",
}


def _as_number(v: object) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        cleaned = v.replace(",", "").replace("$", "").strip().rstrip("%")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _values_match(a: object, b: object, *, numeric: bool) -> bool:
    """Equality with numeric tolerance (3 == 3.0 == "3"); lists/strings exact."""
    if numeric:
        na, nb = _as_number(a), _as_number(b)
        if na is not None and nb is not None:
            return abs(na - nb) < 1e-6
    if isinstance(a, list) and isinstance(b, list):
        return a == b
    return str(a).strip() == str(b).strip()


class ExtractionAdapter:
    """The spec-60 crawler extractor, plugged into the shared harness (§5)."""

    # ── Adapter self-description (read by the harness + the §62 surface) ──
    consumer = CONSUMER
    title = "Extraction"
    spec = "60"
    file = "ai/evals/extraction_adapter.py"
    status = "live"
    produce_blurb = "Run the grounded SourceExtractionAgent on a labeled source page."
    rubric_blurb = "Per-field P/R/F1, no-fabrication (hard floor), schema-validity, normalization."
    materialize_blurb = (
        "A correction, a selector break, or a low-confidence write becomes a golden page."
    )
    materialize_source = "corrections · selector breaks · low-confidence writes"

    def __init__(self) -> None:
        self._agent = SourceExtractionAgent()

    # ── Hook 1: produce (run the extractor; deterministic by default) ────────
    def produce(self, case: EvalCase) -> ExtractionResult:
        return self._agent.extract(case.domain or "", case.payload)

    # ── Hook 2: rubric (the scored dimensions) ───────────────────────────────
    def rubric_dimensions(self) -> tuple[DimensionSpec, ...]:
        return (
            DimensionSpec(
                "per_field_prf",
                "Per-field P/R/F1",
                hard_floor=False,
                kind="deterministic",
                summary="Precision / recall / F1 of emitted (field, value) pairs vs the gold page.",
            ),
            DimensionSpec(
                "no_fabrication",
                "No fabrication",
                hard_floor=True,
                kind="deterministic",
                summary="Every emitted field is grounded in the source and the schema allowlist.",
            ),
            DimensionSpec(
                "schema_validity",
                "Schema validity",
                hard_floor=False,
                kind="deterministic",
                summary="No field outside the domain schema's writable field set.",
            ),
            DimensionSpec(
                "normalization",
                "Normalization",
                hard_floor=False,
                kind="deterministic",
                summary="Numeric fields coerced to numbers, matching the labeled value.",
            ),
        )

    def deterministic_checks(self) -> tuple[tuple[str, str], ...]:
        return tuple((n, b) for n, b in _DETERMINISTIC_BLURBS.items())

    # ── Hook 3: materialize (production failure → curated golden page) ───────
    def materialize(self, event: dict[str, Any]) -> EvalCase:
        """Turn a correction / selector-break / low-confidence write into a
        curated golden page so the same extraction failure is gated forever (§5)."""
        domain = event.get("domain") or "occupations"
        payload = event.get("payload") or {
            "format": "structured",
            "trust_tier": int(event.get("trust_tier", 2)),
            "data": event.get("data", {}) or {},
        }
        expected = event.get("expected") or event.get("corrected_fields") or {}
        reason = event.get("reason") or event.get("kind") or "correction"
        raw_id = event.get("id") or event.get("source_url") or reason
        return EvalCase(
            id=f"prod_{str(raw_id)[:16]}",
            consumer=self.consumer,
            domain=domain,
            payload=payload,
            expected=dict(expected),
            dimension="per_field_prf",
            context={"reason": reason},
            source="production",
        )

    # ── Shared harness hook: score one case (fully deterministic) ────────────
    async def score_case(self, case: EvalCase, *, real: bool) -> CaseScore:
        """Score one labeled page. The core dimensions need no model, so this
        runs identically in deterministic (CI) and real mode — the hard floor
        gates with no API key. ``real`` is accepted for protocol symmetry and
        reserved for the future independent-judge refinement (§4)."""
        result = self.produce(case)
        extracted = result.values()
        expected: dict[str, Any] = dict(case.expected or {})
        schema = schema_for(case.domain or "")
        valid_fields = set(schema.fields) if schema else set()
        numeric_fields = set(schema.numeric_fields) if schema else set()

        # ── per-field P/R/F1 ──
        tp = fp = fn = 0
        for fname, gold in expected.items():
            got = extracted.get(fname, _SENTINEL)
            if got is not _SENTINEL and _values_match(got, gold, numeric=fname in numeric_fields):
                tp += 1
            else:
                fn += 1
        for fname, got in extracted.items():
            gold = expected.get(fname, _SENTINEL)
            if gold is _SENTINEL or not _values_match(got, gold, numeric=fname in numeric_fields):
                fp += 1
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        # ── no_fabrication (hard floor) ──
        grounded = self._agent.verify_grounded(result, case.payload)
        all_in_schema = all(f in valid_fields for f in extracted) if valid_fields else True
        no_fabrication = 1.0 if (grounded and all_in_schema) else 0.0

        # ── schema_validity ──
        schema_validity = (
            (sum(1 for f in extracted if f in valid_fields) / len(extracted))
            if extracted and valid_fields
            else 1.0
        )

        # ── normalization ──
        num_present = [f for f in numeric_fields if f in extracted and f in expected]
        if num_present:
            ok = sum(1 for f in num_present if _as_number(extracted[f]) is not None)
            normalization = ok / len(num_present)
        else:
            normalization = 1.0

        deterministic_passed = no_fabrication >= 1.0 and schema_validity >= 1.0
        passed = deterministic_passed and f1 >= _MIN_F1 and normalization >= _MIN_NORMALIZATION
        return CaseScore(
            case_id=case.id,
            consumer=self.consumer,
            deterministic_passed=deterministic_passed,
            dimension_scores={
                "per_field_prf": round(f1, 4),
                "no_fabrication": no_fabrication,
                "schema_validity": round(schema_validity, 4),
                "normalization": round(normalization, 4),
            },
            passed=passed,
            mode="deterministic",
            detail={
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": round(precision, 3),
                "recall": round(recall, 3),
            },
        )


# Distinct from None so a legitimately-null expected/extracted value is not a hit.
_SENTINEL: Any = object()
