"""Spec 60 §6 step (4) — normalization.

Deterministic maps only (units / SOC / CIP / CEFR / currency / grading-scale).
No LLM: normalization must be reproducible and auditable. Applied after
extraction, before entity resolution, so the reference projection stores clean,
comparable values.
"""

from __future__ import annotations

import re

# CEFR equivalency for the common English tests (§3.7 language equivalency). Maps
# a band to the normalized CEFR level the matcher compares against.
_CEFR_BY_TEST_BAND: dict[str, list[tuple[float, str]]] = {
    "TOEFL_IBT": [(95, "C1"), (72, "B2"), (42, "B1"), (0, "A2")],
    "IELTS": [(7.0, "C1"), (5.5, "B2"), (4.0, "B1"), (0, "A2")],
    "DUOLINGO": [(120, "C1"), (95, "B2"), (65, "B1"), (0, "A2")],
}

_CURRENCY_SYMBOL = {"$": "USD", "£": "GBP", "€": "EUR", "¥": "JPY", "₹": "INR", "C$": "CAD"}


def normalize_soc(code: str) -> str:
    """O*NET 19-1042.00 / BLS 19-1042 → canonical ``19-1042`` form."""
    # Drop the O*NET detail suffix (".00") first, then keep digits + dash.
    base = str(code).split(".")[0]
    return re.sub(r"[^0-9-]", "", base).strip("-")


def normalize_cip(code: str) -> str:
    """CIP ``11.0701`` family — keep digits + the dot; pad to NN.NNNN when short."""
    cleaned = re.sub(r"[^0-9.]", "", str(code))
    if "." not in cleaned and len(cleaned) >= 2:
        cleaned = f"{cleaned[:2]}.{cleaned[2:]}"
    return cleaned


def normalize_currency(raw: str | None) -> str:
    if not raw:
        return "USD"
    raw = raw.strip()
    if raw in _CURRENCY_SYMBOL:
        return _CURRENCY_SYMBOL[raw]
    up = raw.upper()
    return up if len(up) == 3 and up.isalpha() else "USD"


def cefr_for(test_code: str, score: float) -> str | None:
    bands = _CEFR_BY_TEST_BAND.get(test_code.upper())
    if not bands:
        return None
    for threshold, level in bands:
        if score >= threshold:
            return level
    return None


def gpa_to_4_scale(value: float, scale_max: float = 100.0) -> float | None:
    """Coarse grading-scale normalization (e.g. 85/100 → ~3.4 on a 4.0 scale).
    Deterministic linear map; the international service owns the credentialed
    version — this is the reference-side approximation."""
    if scale_max <= 0:
        return None
    if scale_max == 4.0:
        return round(value, 2)
    return round(min(4.0, max(0.0, value / scale_max * 4.0)), 2)


class Normalizer:
    """Applies the domain-appropriate normalizations to an extracted values dict."""

    def normalize(self, domain: str, values: dict) -> dict:
        out = dict(values)
        if domain == "occupations" and "soc_code" in out:
            out["soc_code"] = normalize_soc(out["soc_code"])
        if domain == "majors" and "cip_code" in out:
            out["cip_code"] = normalize_cip(out["cip_code"])
        if "currency" in out:
            out["currency"] = normalize_currency(out.get("currency"))
        if "salary_currency" in out:
            out["salary_currency"] = normalize_currency(out.get("salary_currency"))
        # Code fields → upper, trimmed (tests, visas).
        for key in ("code",):
            if key in out and isinstance(out[key], str):
                out[key] = out[key].strip().upper()
        return out
