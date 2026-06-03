"""Spec 72 §1-§3 — verification & integrity (deterministic). Pure functions."""

from __future__ import annotations

from unipaith.services.verification import (
    content_hash,
    cross_field_anomalies,
    trust_score,
)


def test_content_hash_is_stable_and_tamper_evident():
    h1 = content_hash("Transcript: GPA 3.8")
    assert h1 == content_hash("Transcript: GPA 3.8")  # stable
    assert h1 == content_hash(b"Transcript: GPA 3.8")  # bytes == text
    assert h1 != content_hash("Transcript: GPA 3.9")  # any change → different hash
    assert len(h1) == 64  # sha-256 hex


def test_cross_field_anomalies():
    assert cross_field_anomalies({"gpa": 3.8, "gre": 328}) == []  # consistent
    assert "gpa" in cross_field_anomalies({"gpa": 5.2})[0]  # GPA above scale
    assert cross_field_anomalies({"gpa": 92, "gpa_scale": 100}) == []  # 100-scale ok
    grad_before = cross_field_anomalies({"enrollment_year": 2022, "graduation_year": 2020})
    assert grad_before and "before" in grad_before[0]
    assert cross_field_anomalies({"gre": 400})  # GRE out of 260–340 range
    future = cross_field_anomalies({"graduation_year": 2099}, current_year=2026)
    assert future and "future" in future[0]


def test_trust_score_bands():
    clean = trust_score(documents_total=3, documents_verified=3)
    assert clean["trust_band"] == "high" and clean["requires_human_review"] is False

    flagged = trust_score(
        anomaly_count=2, documents_total=4, documents_verified=1, duplicate_likelihood=0.5
    )
    assert flagged["trust_band"] in ("medium", "low")
    assert flagged["requires_human_review"] is True
    assert 0.0 <= flagged["trust_score"] <= 1.0

    # A strong duplicate-identity signal alone drops trust out of "high".
    dup = trust_score(duplicate_likelihood=0.9)
    assert dup["trust_band"] != "high"
