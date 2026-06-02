"""Spec 44 — Adaptive Intake Engine service package.

``registry`` holds the pure signal schema (no DB); ``intake_engine_service``
holds the §3 per-signal pipeline and the §4 completeness/readiness gates.
"""

from unipaith.services.intake.intake_engine_service import IntakeEngineService

__all__ = ["IntakeEngineService"]
