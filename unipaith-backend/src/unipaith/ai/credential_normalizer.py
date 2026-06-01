"""CredentialNormalizer — Spec 38 §2.1 / §5 (extends DocumentParseTriage 45 §19).

Maps a foreign academic grade onto the program's 4.0 GPA scale so an admissions
reviewer sees raw + normalized side by side.

Two layers:
- :func:`deterministic_normalize` — a pure-Python grading-scale mapper covering
  the systems the spec names (UK, IB, A-level, Gaokao, 10-point, percentage).
  Always available; it is both the default and the fallback.
- :func:`normalize_credential` — the optional Haiku-tier agent (gated by
  ``ai_international_v2_enabled``) that refines the mapping and adds a course-map
  note. On any failure (flag off / mock / parse / provider) it returns ``None``
  and the caller keeps the deterministic result — the Plan-2 invariant: never
  raise to the caller, AI never decides feasibility.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.credential_normalizer_schema import SUBMIT_NORMALIZATION_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT = (PROMPTS_DIR / "credential_normalizer.md").read_text(encoding="utf-8").rstrip()

AGENT_NAME = "credential_normalizer"

# ── Deterministic grading-scale bands (→ 4.0) ───────────────────────────────
# Discrete bands chosen so the spec example holds: 85/100 → 3.6.
_PCT_BANDS: list[tuple[float, float]] = [
    (90, 4.0),
    (85, 3.6),
    (80, 3.3),
    (75, 3.0),
    (70, 2.7),
    (65, 2.3),
    (60, 2.0),
    (0, 1.0),
]
_UK_BANDS: list[tuple[float, float]] = [
    (70, 4.0),  # First
    (60, 3.7),  # Upper Second (2:1)
    (50, 3.0),  # Lower Second (2:2)
    (40, 2.3),  # Third
    (0, 1.0),
]
_IB_BANDS: list[tuple[float, float]] = [
    (42, 4.0),
    (38, 3.7),
    (34, 3.3),
    (30, 3.0),
    (26, 2.7),
    (24, 2.3),
    (0, 1.0),
]
# A-level single-grade letters → 4.0.
_ALEVEL_MAP: dict[str, float] = {
    "A*": 4.0,
    "A": 4.0,
    "B": 3.7,
    "C": 3.3,
    "D": 3.0,
    "E": 2.7,
}


def _band(value: float, bands: list[tuple[float, float]]) -> float:
    for threshold, gpa in bands:
        if value >= threshold:
            return gpa
    return bands[-1][1]


def _q(value: float) -> Decimal:
    """Quantize to two decimals, capped at 4.0."""
    return Decimal(str(round(min(value, 4.0), 2)))


def deterministic_normalize(
    raw_gpa: Decimal | float | None,
    *,
    scale_hint: str | None = None,
    country: str | None = None,
) -> tuple[Decimal | None, str]:
    """Map a foreign grade to a 4.0 GPA. Returns ``(normalized, source_label)``.

    ``scale_hint`` is a free-text grading-system label (e.g. "percentage",
    "UK", "IB", "10-point", "Gaokao", "A-level", "4.0"). When absent the system
    is inferred from the value's magnitude. Returns ``(None, "")`` when there is
    no usable input.
    """
    # A-level letter grades arrive as a hint/string rather than a number.
    h = (scale_hint or "").strip().lower()
    c = (country or "").strip().lower()
    if "a-level" in h or "a level" in h or "alevel" in h:
        # The raw value may be a letter grade encoded in the hint.
        for letter, gpa in _ALEVEL_MAP.items():
            if h.rstrip().endswith(letter.lower()):
                return _q(gpa), f"A-level {letter}"

    if raw_gpa is None:
        return None, ""
    try:
        raw = float(raw_gpa)
    except (TypeError, ValueError):
        return None, ""
    if raw < 0:
        return None, ""

    if "ib" in h:
        return _q(_band(raw, _IB_BANDS)), f"IB {raw:g}/45"
    if "uk" in h or "british" in h:
        return _q(_band(raw, _UK_BANDS)), f"UK {raw:g}/100"
    if "gaokao" in h or "gaokao" in c:
        pct = raw / 7.5 if raw > 100 else raw  # Gaokao is often out of 750
        return _q(_band(pct, _PCT_BANDS)), f"Gaokao {raw:g}"
    if ("10" in h and "100" not in h) or "cgpa" in h:
        return _q(raw / 10 * 4.0), f"{raw:g}/10"
    if "percent" in h or "100" in h:
        return _q(_band(raw, _PCT_BANDS)), f"{int(round(raw))}/100"
    if "4" in h:  # already a 4.0-style GPA
        return _q(raw), "4.0 scale"

    # No hint — infer from magnitude.
    if raw > 10:  # percentage-like (or Gaokao out of 750)
        pct = raw if raw <= 100 else raw / 7.5
        return _q(_band(pct, _PCT_BANDS)), f"{int(round(pct))}/100"
    if raw <= 4.0:
        return _q(raw), "4.0 scale"
    # 4 < raw <= 10 → treat as a 10-point CGPA
    return _q(raw / 10 * 4.0), f"{raw:g}/10"


def _payload(
    raw_gpa: float, scale_hint: str | None, country: str | None, degree_type: str | None
) -> str:
    return json.dumps(
        {
            "raw_gpa": raw_gpa,
            "grading_system": scale_hint or "unknown",
            "country": country or "unknown",
            "degree_level": degree_type or "unknown",
            "target_scale": "4.0",
        },
        ensure_ascii=False,
    )


def _parse(blocks: list[dict[str, Any]]) -> dict | None:
    for b in blocks:
        if b.get("type") == "tool_use" and b.get("name") == "submit_normalization":
            data = b.get("input") or {}
            gpa = data.get("normalized_gpa")
            if gpa is None:
                return None
            try:
                norm = _q(float(gpa))
            except (TypeError, ValueError):
                return None
            return {
                "normalized_gpa": norm,
                "source_scale": str(data.get("source_scale") or "").strip()[:60],
                "course_map_note": str(data.get("course_map_note") or "").strip()[:400] or None,
                "confidence": str(data.get("confidence") or "medium"),
            }
    return None


async def normalize_credential(
    *,
    raw_gpa: Decimal | float | None,
    scale_hint: str | None = None,
    country: str | None = None,
    degree_type: str | None = None,
    client: AIClient | None = None,
) -> dict | None:
    """Return a refined normalization dict, or ``None`` to keep the deterministic
    result. Best-effort; never raises."""
    if raw_gpa is None:
        return None
    try:
        cl = client or get_client()
        payload = _payload(float(raw_gpa), scale_hint, country, degree_type)
        response = await cl.message(
            agent=AGENT_NAME,
            model="haiku",
            system=[{"type": "text", "text": _PROMPT, "cache_control": CACHE_1H}],
            messages=[{"role": "user", "content": payload}],
            tools=[{**SUBMIT_NORMALIZATION_TOOL, "cache_control": CACHE_1H}],
            tool_choice={"type": "tool", "name": "submit_normalization"},
            max_tokens=400,
            temperature=0.0,
            surface="international",
        )
        return _parse(response.content_blocks)
    except Exception as exc:  # noqa: BLE001 — normalization is best-effort
        logger.info("CredentialNormalizer fell back to deterministic mapper: %s", exc)
        return None
