"""Spec 72 §1-§3 — verification & integrity (deterministic core).

The trust layer the papers' Review stage needs (authenticate materials, rule out
fraud, `Master Paper`:90): tamper-evidence hashing (ApplyProof-style), deterministic
cross-field anomaly detection, and a composite trust score. Everything here is a
**flag for human review, never an accusation or an auto-decision** — the human-in-
the-loop invariant (`Master Paper`:88). The LLM authenticity scorer
(`ai/authenticity`) enriches these; this rule-based floor always runs.
"""

from __future__ import annotations

import hashlib
from typing import Any

# Standardized-test plausible ranges (cross-field anomaly input, §3).
_TEST_RANGES: dict[str, tuple[float, float]] = {
    "gre": (260, 340),
    "gmat": (200, 800),
    "toefl": (0, 120),
    "ielts": (0, 9),
    "sat": (400, 1600),
    "act": (1, 36),
}


def content_hash(data: str | bytes) -> str:
    """Tamper-evidence: a stable SHA-256 of a document's content. A re-uploaded or
    altered document yields a different hash → a mismatch against the stored hash
    flags tampering (the cryptographic verification ApplyProof provides, §2)."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def cross_field_anomalies(fields: dict[str, Any], *, current_year: int | None = None) -> list[str]:
    """Deterministic cross-field consistency checks (§3 anomaly input). Returns
    human-readable anomaly descriptions (empty = consistent). Flags for review —
    never an accusation."""
    anomalies: list[str] = []

    gpa = fields.get("gpa")
    gpa_scale = fields.get("gpa_scale", 4.0)
    if gpa is not None and (gpa < 0 or gpa > gpa_scale):
        anomalies.append(f"gpa {gpa} outside 0–{gpa_scale}")

    enroll = fields.get("enrollment_year")
    grad = fields.get("graduation_year")
    if enroll and grad and grad < enroll:
        anomalies.append(f"graduation_year {grad} before enrollment_year {enroll}")

    for test, (lo, hi) in _TEST_RANGES.items():
        v = fields.get(test)
        if v is not None and (v < lo or v > hi):
            anomalies.append(f"{test} {v} outside {lo}–{hi}")

    if current_year is not None:
        for key in ("graduation_year", "enrollment_year"):
            y = fields.get(key)
            if y is not None and y > current_year + 8:  # implausibly far future
                anomalies.append(f"{key} {y} implausibly far in the future")

    return anomalies


def trust_score(
    *,
    anomaly_count: int = 0,
    documents_total: int = 0,
    documents_verified: int = 0,
    duplicate_likelihood: float = 0.0,
) -> dict:
    """Composite trust score in [0,1] + band. Deterministic: starts at 1.0; each
    anomaly, each unverified document, and duplicate-identity likelihood reduce
    it. Drives **triage priority for a human reviewer**, never an auto-reject."""
    score = 1.0
    score -= min(0.5, 0.1 * max(0, anomaly_count))
    if documents_total > 0:
        unverified_ratio = 1 - (max(0, documents_verified) / documents_total)
        score -= 0.3 * max(0.0, min(1.0, unverified_ratio))
    score -= 0.4 * max(0.0, min(1.0, duplicate_likelihood))
    score = round(max(0.0, min(1.0, score)), 4)
    band = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
    return {
        "trust_score": score,
        "trust_band": band,
        "anomaly_count": max(0, anomaly_count),
        "requires_human_review": band != "high",
    }
