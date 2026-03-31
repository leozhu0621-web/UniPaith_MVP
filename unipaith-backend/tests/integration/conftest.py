"""
Integration test configuration.

These tests require real GPU infrastructure (AWS or local).
Skipped by default — run with: pytest -m gpu
"""
from __future__ import annotations

import os

import pytest

# Skip all tests in this directory unless GPU_TEST=true
if os.environ.get("GPU_TEST", "").lower() != "true":
    pytest.skip("GPU tests disabled (set GPU_TEST=true)", allow_module_level=True)
