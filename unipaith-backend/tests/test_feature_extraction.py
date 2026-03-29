"""
Tests for feature extraction logic — normalization functions and structured feature computation.
All tests use AI_MOCK_MODE=true.
"""

import os

os.environ["AI_MOCK_MODE"] = "true"

import pytest

from unipaith.ai.feature_extraction import FeatureExtractor


class TestGPANormalization:
    def setup_method(self):
        # FeatureExtractor needs a db, but normalization helpers don't use it
        self.extractor = FeatureExtractor.__new__(FeatureExtractor)

    def test_normalize_gpa_4_scale(self):
        assert self.extractor._normalize_gpa(3.7, "4.0") == pytest.approx(0.925)

    def test_normalize_gpa_percentage(self):
        assert self.extractor._normalize_gpa(85, "percentage") == pytest.approx(0.85)

    def test_normalize_gpa_10_scale(self):
        assert self.extractor._normalize_gpa(8.5, "10.0") == pytest.approx(0.85)

    def test_normalize_gpa_ib(self):
        assert self.extractor._normalize_gpa(38, "ib") == pytest.approx(38 / 45)

    def test_normalize_gpa_5_scale(self):
        assert self.extractor._normalize_gpa(4.2, "5.0") == pytest.approx(0.84)

    def test_normalize_gpa_7_scale(self):
        assert self.extractor._normalize_gpa(6.0, "7.0") == pytest.approx(6.0 / 7.0)

    def test_normalize_gpa_unknown_scale(self):
        assert self.extractor._normalize_gpa(3.5, "french") is None

    def test_normalize_gpa_caps_at_1(self):
        assert self.extractor._normalize_gpa(4.5, "4.0") == 1.0


class TestTestScoreNormalization:
    def setup_method(self):
        self.extractor = FeatureExtractor.__new__(FeatureExtractor)

    def test_normalize_sat(self):
        assert self.extractor._normalize_test_score("SAT", 1400) == pytest.approx(1400 / 1600)

    def test_normalize_gre(self):
        assert self.extractor._normalize_test_score("GRE", 325) == pytest.approx(325 / 340)

    def test_normalize_gmat(self):
        assert self.extractor._normalize_test_score("GMAT", 720) == pytest.approx(720 / 800)

    def test_normalize_toefl(self):
        assert self.extractor._normalize_test_score("TOEFL", 105) == pytest.approx(105 / 120)

    def test_normalize_ielts(self):
        assert self.extractor._normalize_test_score("IELTS", 7.5) == pytest.approx(7.5 / 9)

    def test_normalize_act(self):
        assert self.extractor._normalize_test_score("ACT", 32) == pytest.approx(32 / 36)

    def test_normalize_none_score(self):
        assert self.extractor._normalize_test_score("GRE", None) is None

    def test_normalize_unknown_test(self):
        assert self.extractor._normalize_test_score("UNKNOWN_TEST", 100) is None

    def test_case_insensitive(self):
        assert self.extractor._normalize_test_score("gre", 325) == pytest.approx(325 / 340)
