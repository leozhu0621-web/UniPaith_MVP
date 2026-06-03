"""Spec 66 §6 — deterministic prospect segmentation bands. Pure functions."""

from __future__ import annotations

from unipaith.services.taste_segmentation import (
    fit_to_program_band,
    likelihood_to_apply_band,
    nurture_band,
    segment_prospect,
)

_REQ = {"min_gpa": 3.5, "min_test": 320, "fields_cip": ["11"]}


def test_fit_band():
    strong = {"gpa": 3.9, "test_score": 330, "cip_family": "11"}
    assert fit_to_program_band(strong, _REQ) == "high"
    weak = {"gpa": 2.8, "test_score": 280, "cip_family": "52"}
    assert fit_to_program_band(weak, _REQ) == "low"
    # No signals → neutral medium (not a false high/low).
    assert fit_to_program_band({}, _REQ) == "medium"


def test_likelihood_band():
    assert likelihood_to_apply_band({"saved": 1, "events_attended": 1, "page_views": 2}) == "high"
    assert likelihood_to_apply_band({"page_views": 3}) == "medium"
    assert likelihood_to_apply_band({}) == "low"


def test_nurture_band():
    # High interest + low readiness → nurture.
    assert nurture_band("low", "high") == "nurture_needed"
    assert nurture_band("medium", "low", following=True) == "nurture_needed"
    # Strong fit → ready.
    assert nurture_band("high", "low") == "ready"
    # Low fit, no interest → monitor.
    assert nurture_band("low", "low") == "monitor"


def test_segment_prospect_end_to_end():
    seg = segment_prospect(
        {"gpa": 2.9, "cip_family": "11", "following": True},
        _REQ,
        {"saved": 2, "events_attended": 1},
    )
    assert set(seg) == {"fit_band", "likelihood_band", "nurture_band"}
    assert seg["likelihood_band"] == "high"
    assert seg["nurture_band"] == "nurture_needed"  # engaged but not yet a strong fit
