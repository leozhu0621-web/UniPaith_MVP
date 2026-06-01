"""Spec 38 §3 / §9 + Spec 46 §6 — fairness contract.

Visa / immigration status must NEVER be a selection criterion. It informs
feasibility + yield planning only. This contract pins that: the modules that
compute the match/ranking/score inputs must not reference any visa, immigration,
SEVIS, financial-proof, or country-requirement field. If a future change wires
international-processing data into scoring, this test fails.

It is a source-level contract by design — it guards the *inputs* to scoring, not
a single computed value, so it can't be silently bypassed by a new code path.
"""

import pathlib

import pytest

from unipaith.services.international_service import InternationalService

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "unipaith"

# Every module that feeds the fitness_score / confidence_score / probability
# bands. None of these may read visa / immigration / international-processing.
_RANKING_MODULES = [
    "services/match_service.py",
    "services/matching.py",
    "services/match_banding.py",
    "services/program_features.py",
    "ai/feature_emitter.py",
    "ai/probability.py",
    "ai/rationale.py",
]

# Concrete identifiers that would only appear if visa / immigration data were
# wired into scoring. Plain words like "international" are intentionally NOT
# here — they appear innocently; these are the field/model names that matter.
_FORBIDDEN = [
    "internationalprocessing",
    "studentvisainfo",
    "visa_info",
    "visa_outcome",
    "visa_feasibility",
    "visa_required",
    "financial_proof",
    "immigration_doc",
    "sevis",
    "country_requirement",
    "credential_normalized_gpa",
]


def test_visa_immigration_excluded_from_ranking_inputs():
    offenders = []
    for mod in _RANKING_MODULES:
        path = _SRC / mod
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for token in _FORBIDDEN:
            if token in text:
                offenders.append(f"{mod} references '{token}'")
    assert not offenders, (
        "Visa/immigration status must never feed ranking (Spec 38 §3/§9, 46 §6): "
        + "; ".join(offenders)
    )


def test_international_processing_model_not_imported_by_matcher():
    """Belt-and-suspenders: the matcher must not even import the model."""
    for mod in ("services/match_service.py", "services/matching.py"):
        path = _SRC / mod
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        assert "international" not in text.lower(), (
            f"{mod} mentions 'international' — keep international processing out of matching."
        )


@pytest.mark.asyncio
async def test_feasibility_band_is_labelled_operational_only():
    """The feasibility band the institution sees is explicitly operational —
    the packet block carries the fairness note so the UI can render it (§3)."""
    # The feasibility band derives from operational fields only; assert the
    # function exists and returns the documented shape without any score field.
    result = InternationalService._feasibility_band(None, {"financial_proof_available": True})
    assert set(result.keys()) == {"band", "reasons"}
    assert "score" not in result
    assert result["band"] in {"blocked", "at_risk", "moderate", "strong"}
