"""Spec 60 §13 — the SourceExtractionAgent.

Input: a cleaned source payload + a target ``DomainSchema``. Output: structured
fields, each with a per-field confidence and a source span / key as evidence.

Hard invariant (§15): **never invents**. A field is emitted ONLY when it is
grounded in the provided source — a present key for the structured (Tier-1/2)
path, or a regex match within the source text for the free-text (Tier-3/4) path.
``verify_grounded`` re-checks every emitted field against the raw source, and the
enrichment writer trusts only verified output. The deterministic templates here
are the default; the Qwen/Claude path (``ai_crawler_extraction_v2_enabled``) is a
drop-in that passes through the *same* grounding verification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from unipaith.config import settings
from unipaith.services.crawler.schemas import DomainSchema, schema_for

# Confidence by source tier (§8): official bulk lands trusted; aggregator / free
# text is lower and may need corroboration before auto-apply.
_TIER_CONFIDENCE = {1: 0.95, 2: 0.85, 3: 0.65, 4: 0.45}
_TEXT_CONFIDENCE_PENALTY = 0.15


@dataclass
class ExtractedField:
    value: object
    confidence: float
    evidence: str  # "key:<k>" for structured, or the matched span for text
    grounded: bool = True


@dataclass
class ExtractionResult:
    domain: str
    fields: dict[str, ExtractedField] = field(default_factory=dict)
    source_kind: str = "structured"  # structured | text
    used_llm: bool = False

    def values(self) -> dict[str, object]:
        return {k: f.value for k, f in self.fields.items()}


def _coerce_number(raw: object) -> float | int | None:
    if isinstance(raw, (int, float)):
        return raw
    if not isinstance(raw, str):
        return None
    cleaned = raw.replace(",", "").replace("$", "").strip().rstrip("%")
    try:
        num = float(cleaned)
    except ValueError:
        return None
    return int(num) if num.is_integer() else num


class SourceExtractionAgent:
    """Stateless, deterministic-by-default extractor. One instance per pipeline."""

    def extract(self, domain: str, payload: dict) -> ExtractionResult:
        """``payload`` is ``{"format": "structured", "data": {...}}`` (the Tier-1/2
        bulk path) or ``{"format": "text", "text": "..."}`` (the Tier-3/4 crawl
        path)."""
        schema = schema_for(domain)
        if schema is None:
            return ExtractionResult(domain=domain, fields={})

        fmt = payload.get("format", "structured")
        tier = int(payload.get("trust_tier", 2))
        base_conf = _TIER_CONFIDENCE.get(tier, 0.6)

        if fmt == "structured":
            result = self._extract_structured(schema, payload.get("data", {}), base_conf)
        else:
            result = self._extract_text(schema, payload.get("text", "") or "", base_conf)

        # The LLM path is a drop-in that must still pass grounding verification.
        if settings.ai_crawler_extraction_v2_enabled:
            llm = self._extract_llm(schema, payload, base_conf)
            if llm is not None:
                result = llm
        # Final safety net: drop anything not grounded in the source (§15).
        self._enforce_grounding(result, payload)
        return result

    def _extract_structured(
        self, schema: DomainSchema, data: dict, base_conf: float
    ) -> ExtractionResult:
        res = ExtractionResult(domain=schema.domain, source_kind="structured")
        if not isinstance(data, dict):
            return res
        for name in schema.fields:
            if name not in data:
                continue  # absent key → never emitted (no fabrication)
            raw = data[name]
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                continue
            value = _coerce_number(raw) if name in schema.numeric_fields else raw
            if value is None:
                continue
            res.fields[name] = ExtractedField(
                value=value, confidence=base_conf, evidence=f"key:{name}"
            )
        return res

    def _extract_text(self, schema: DomainSchema, text: str, base_conf: float) -> ExtractionResult:
        res = ExtractionResult(domain=schema.domain, source_kind="text")
        conf = max(0.3, base_conf - _TEXT_CONFIDENCE_PENALTY)
        for name, pattern in schema.text_patterns.items():
            m = re.search(pattern, text)
            if not m:
                continue
            captured = m.group(1)
            value = _coerce_number(captured) if name in schema.numeric_fields else captured
            if value is None:
                continue
            res.fields[name] = ExtractedField(
                value=value, confidence=conf, evidence=m.group(0)[:120]
            )
        return res

    def _extract_llm(
        self, schema: DomainSchema, payload: dict, base_conf: float
    ) -> ExtractionResult | None:
        """Qwen/Claude extraction (§13). Forced structured output, schema-validated.
        Returns ``None`` to fall back to the deterministic path when no ML endpoint
        is reachable — the codebase-wide "LLM augments, never gates" rule. The
        returned fields still go through ``_enforce_grounding``, so even a
        hallucinating model can't write an ungrounded field."""
        # No live ML endpoint in this environment → deterministic fallback. The
        # seam is here so 63's Qwen extractor drops in without touching callers.
        return None

    def _enforce_grounding(self, result: ExtractionResult, payload: dict) -> None:
        """Drop any field whose value can't be traced back to the source — the
        structural guarantee behind the no-fabrication acceptance test."""
        fmt = payload.get("format", "structured")
        if fmt == "structured":
            data = payload.get("data", {}) or {}
            present = set(data.keys()) if isinstance(data, dict) else set()
            for name in list(result.fields):
                if name not in present:
                    del result.fields[name]
        else:
            text = (payload.get("text", "") or "").lower()
            for name, f in list(result.fields.items()):
                ev = (f.evidence or "").lower()
                if not ev or ev not in text:
                    del result.fields[name]

    def verify_grounded(self, result: ExtractionResult, payload: dict) -> bool:
        """True iff every emitted field is grounded in the source. Used by tests
        and by the writer as a pre-write assertion."""
        fmt = payload.get("format", "structured")
        if fmt == "structured":
            present = set((payload.get("data") or {}).keys())
            return all(name in present for name in result.fields)
        text = (payload.get("text", "") or "").lower()
        return all((f.evidence or "").lower() in text for f in result.fields.values())
