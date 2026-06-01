"""Spec 26 §11 — segment rule tree + NL bridge tests."""

from __future__ import annotations

import pytest

from unipaith.ai.segment_builder import _keyword_fallback, build_rules_from_nl
from unipaith.services.segment_resolver import _intersect, _union


def test_rule_tree_intersect_union():
    a = [1, 2, 3]
    b = [2, 3, 4]
    assert set(_intersect(a, b)) == {2, 3}
    assert set(_union(a, b)) == {1, 2, 3, 4}


def test_keyword_fallback_saved_program():
    result = _keyword_fallback("students who saved Engineering programs")
    fields = [r["field"] for r in result["rules"]]
    assert "engagement.saved_program" in fields
    assert result["confidence_overall"] >= 50


def test_keyword_fallback_not_started():
    result = _keyword_fallback("high interest prospects who haven't started an app")
    fields = [r["field"] for r in result["rules"]]
    assert "application.not_submitted" in fields


@pytest.mark.asyncio
async def test_nl_bridge_mock_mode():
    result = await build_rules_from_nl("students who viewed our page in the last 30 days")
    assert "rules" in result
    assert len(result["rules"]) >= 1
    assert "confidence_overall" in result
