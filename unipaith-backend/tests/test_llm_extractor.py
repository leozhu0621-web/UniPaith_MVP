"""Tests for Phase 5 – LLMExtractor helpers."""
from __future__ import annotations

from decimal import Decimal

import pytest

from unipaith.crawler.extractor import LLMExtractor




async def test_confidence_computation_high():
    """Complete data should yield high confidence."""
    data = {
        "institution_name": "MIT",
        "program_name": "Computer Science MS",
        "degree_type": "Masters",
        "department": "EECS",
        "tuition": 55000,
        "application_deadline": "2026-01-15",
        "description_text": "A great program.",
        "requirements": {"gpa": 3.5},
        "institution_country": "US",
        "institution_city": "Cambridge",
        "duration_months": 24,
        "acceptance_rate": 0.12,
        "highlights": ["top ranked"],
        "faculty_contacts": [{"name": "Prof X"}],
        "rankings": {"us_news": 1},
        "financial_aid_info": {"available": True},
    }
    overall, field_confs = LLMExtractor._compute_confidence(data)
    assert overall >= Decimal("0.90")
    assert field_confs["institution_name"] == 1.0


async def test_confidence_computation_low():
    """Minimal data should yield low confidence."""
    data = {
        "institution_name": "Unknown",
        "program_name": "Some Program",
    }
    overall, field_confs = LLMExtractor._compute_confidence(data)
    assert overall < Decimal("0.50")
    assert field_confs["degree_type"] == 0.0


async def test_normalize_degree():
    assert LLMExtractor._normalize_degree_type("phd") == "PhD"
    assert LLMExtractor._normalize_degree_type("master's") == "Masters"
    assert LLMExtractor._normalize_degree_type("mba") == "MBA"
    assert LLMExtractor._normalize_degree_type("m.s.") == "Masters"
    assert LLMExtractor._normalize_degree_type(None) is None
    # Unknown should return as-is (stripped)
    assert LLMExtractor._normalize_degree_type("Custom Degree") == "Custom Degree"
