"""Profile enrichment — bring any profile to the standard using verified data
only. The deterministic verification gate is the no-fabrication safety core; the
engine is conformance-driven and pure given a ``Researcher`` adapter.

See ``docs/superpowers/specs/2026-06-09-profile-standard-and-enrichment-design.md``
(§7 engine, §8 gate).
"""

from .engine import EnrichmentResult, Researcher, apply_patch, enrich, plan
from .gate import Evidence, GateDecision, verify

__all__ = [
    "Evidence",
    "GateDecision",
    "verify",
    "EnrichmentResult",
    "Researcher",
    "enrich",
    "plan",
    "apply_patch",
]
