"""Profile standard — the canonical, versioned blueprint for the three profile
levels (institution / school / program), extracted from the MIT / Sloan / MBAn
reference instance, plus a pure conformance checker.

See ``docs/superpowers/specs/2026-06-09-profile-standard-and-enrichment-design.md``.
"""

from .conformance import ConformanceResult, check_conformance
from .manifest import MANIFEST, SOURCING, STANDARD_VERSION, Field, Section

__all__ = [
    "MANIFEST",
    "SOURCING",
    "STANDARD_VERSION",
    "Field",
    "Section",
    "ConformanceResult",
    "check_conformance",
]
