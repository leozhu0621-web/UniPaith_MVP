"""SegmentBuilderNLBridge — Spec 26 §6 / 45 §17.

Converts a natural-language audience description into structured segment rules
drawn from the platform signal dictionary. Workhorse-tier (Sonnet, forced tool
use). Per the Plan-2 integration invariant, ANY failure (feature flag off, mock
mode, consent/parse/provider error) returns a keyword-parser fallback so the
caller never sees a 5xx — the institution always gets *some* editable rules.

Output: ``{rules: [{field, operator, value, branch, ambiguous}], confidence_overall:int,
ambiguity_notes: [str]}``. ``rules`` is a flat list (matches 45 §17); the
frontend loads include/exclude branches from each rule's ``branch``.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.segment_builder_schema import EMIT_RULES_TOOL
from unipaith.config import settings
from unipaith.services.segment_signals import SIGNAL_REGISTRY

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT = (PROMPTS_DIR / "segment_builder.md").read_text(encoding="utf-8").rstrip()

_FALLBACK_NOTE = "AI assist is in rule-based fallback mode — review the suggested rules carefully."


class SegmentBuilderNLBridge:
    AGENT_NAME = "segment_builder_nl"
    PROMPT_VERSION = "v1"

    def __init__(self, db: AsyncSession | None = None, client: AIClient | None = None):
        self.db = db
        self.client = client or get_client()

    async def convert(self, text: str) -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {
                "rules": [],
                "confidence_overall": 0,
                "ambiguity_notes": ["No description provided."],
            }

        if not settings.ai_segment_builder_v2_enabled:
            return self._fallback(text)

        try:
            payload = json.dumps(
                {"description": text, "available_signals": self._compact_dictionary()},
                ensure_ascii=False,
            )
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="sonnet",
                system=[{"type": "text", "text": _PROMPT, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": payload}],
                tools=[{**EMIT_RULES_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "emit_rules"},
                max_tokens=1500,
                temperature=0.0,
                surface="segments",
                db=self.db,
            )
            parsed = self._parse(response.content_blocks)
            if not parsed:
                return self._fallback(text)
            validated = self._validate(parsed)
            if not validated["rules"]:
                return self._fallback(text)
            return validated
        except Exception as exc:  # noqa: BLE001 — NL bridge is best-effort
            logger.info("SegmentBuilderNLBridge fell back to keyword parser: %s", exc)
            return self._fallback(text)

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _compact_dictionary() -> list[dict[str, Any]]:
        out = []
        for sig in SIGNAL_REGISTRY.values():
            entry: dict[str, Any] = {
                "key": sig.key,
                "label": sig.label,
                "operators": sig.operators,
                "value_type": sig.value_type,
            }
            if sig.options:
                entry["options"] = [o["value"] for o in sig.options]
            out.append(entry)
        return out

    @staticmethod
    def _parse(blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "emit_rules":
                return b.get("input") or {}
        return None

    @staticmethod
    def _validate(parsed: dict[str, Any]) -> dict[str, Any]:
        raw_rules = parsed.get("rules") or []
        notes = list(parsed.get("ambiguity_notes") or [])
        clean: list[dict[str, Any]] = []
        dropped: list[str] = []
        for r in raw_rules:
            if not isinstance(r, dict):
                continue
            field = r.get("field")
            sig = SIGNAL_REGISTRY.get(field)
            if sig is None:
                if field:
                    dropped.append(str(field))
                continue
            operator = r.get("operator")
            if operator not in sig.operators:
                operator = sig.operators[0] if sig.operators else operator
            branch = r.get("branch") if r.get("branch") in ("include", "exclude") else "include"
            clean.append(
                {
                    "field": field,
                    "operator": operator,
                    "value": r.get("value"),
                    "branch": branch,
                    "ambiguous": bool(r.get("ambiguous")),
                }
            )
        if dropped:
            notes.append(
                "Could not map: " + ", ".join(sorted(set(dropped))) + " — no matching signal."
            )
        conf = parsed.get("confidence_overall")
        try:
            conf = max(0, min(100, int(conf)))
        except (TypeError, ValueError):
            conf = 50
        return {"rules": clean, "confidence_overall": conf, "ambiguity_notes": notes[:8]}

    # ── keyword fallback (no LLM) ─────────────────────────────────────────
    @staticmethod
    def _fallback(text: str) -> dict[str, Any]:
        t = text.lower()
        rules: list[dict[str, Any]] = []

        def add(field: str, operator: str, value: Any = None, branch: str = "include") -> None:
            rule: dict[str, Any] = {
                "field": field,
                "operator": operator,
                "branch": branch,
                "ambiguous": True,
            }
            if value is not None:
                rule["value"] = value
            rules.append(rule)

        # degree
        degrees = []
        if re.search(r"\bmaster|\bmsc|\bgraduate|\bgrad\b|\bmba\b", t):
            degrees.append("master")
        if re.search(r"\bbachelor|\bundergrad", t):
            degrees.append("bachelor")
        if re.search(r"\bphd|\bdoctora", t):
            degrees.append("phd")
        if degrees:
            add("saved_program_degree", "in", degrees)

        # activity verbs
        if re.search(r"\bview|visit|looked at|browsed", t):
            add("viewed_institution", "within_days", 30)
        if re.search(r"\bsaved|shortlist|bookmark", t):
            add("saved_program", "exists")
        if re.search(r"\bcompared\b", t):
            add("compared_program", "exists")
        if re.search(r"requested info|inquir|reached out|asked about", t):
            add("requested_info", "exists")
        if re.search(r"attended", t):
            add("event_engagement", "in", ["attended"])
        elif re.search(r"\brsvp|webinar|open house|info session|event", t):
            add("event_engagement", "in", ["rsvp"])

        # fit / likelihood / nurture
        if re.search(r"high[- ]?fit|strong fit|best fit|top match|great match|high match", t):
            add("fit_band", "in", ["high"])
        if re.search(r"likely to apply|high intent|ready to apply", t):
            add("likelihood_band", "in", ["high"])
        if re.search(r"nurtur", t):
            add("nurture_band", "in", ["high"])

        # application state (negation first)
        if re.search(
            r"haven'?t applied|not applied|no application|hasn'?t applied|without applying", t
        ):
            add("started_application", "exists", branch="exclude")
        elif re.search(
            r"started but|didn'?t submit|incomplete application|abandoned|not submitted", t
        ):
            add("started_not_submitted", "exists")
        elif re.search(r"\bapplied\b|applicants?\b", t):
            add("started_application", "exists")

        # modality
        modality = []
        if re.search(r"\bonline\b|remote", t):
            modality.append("online")
        if re.search(r"in[- ]person|on campus|on-campus", t):
            modality.append("in_person")
        if re.search(r"hybrid", t):
            modality.append("hybrid")
        if modality:
            add("modality_pref", "in", modality)

        # budget (e.g. "under $40k", "budget 60k")
        m = re.search(r"(\d{2,3})\s*k", t)
        if m and ("budget" in t or "$" in t or "afford" in t or "tuition" in t):
            amt = int(m.group(1)) * 1000
            band = (
                "under_20k"
                if amt < 20000
                else "20k_40k"
                if amt < 40000
                else "40k_60k"
                if amt < 60000
                else "60k_plus"
            )
            add("budget_band", "in", [band])

        notes = [_FALLBACK_NOTE]
        if not rules:
            notes.append(
                "Could not derive rules from the description — build the segment manually."
            )
        return {"rules": rules, "confidence_overall": 40 if rules else 0, "ambiguity_notes": notes}


_default: SegmentBuilderNLBridge | None = None


def get_segment_builder() -> SegmentBuilderNLBridge:
    global _default
    if _default is None:
        _default = SegmentBuilderNLBridge()
    return _default


def reset_segment_builder() -> None:
    global _default
    _default = None
