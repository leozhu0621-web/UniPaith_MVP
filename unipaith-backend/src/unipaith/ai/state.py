"""Phase A2 — Discovery state machine.

Defines the FSM the orchestrator and validator share. The state machine
drives:

  - which system-prompt mode the orchestrator runs in
  - which exit conditions the validator checks
  - how the session.completion_pct is computed each turn

This is intentionally pure-Python (no DB, no LLM). Callers feed in the
current session state + a snapshot of the student's known profile + the
artifacts harvested so far, and get back:

  - whether the layer is complete
  - what's still missing (used as `next_probe` hints to the orchestrator)
  - the completion percentage for the current track + layer

A2 ships only the BASIC layer's transition logic. PERSONALITY and IDENTITY
exit conditions land in A3, which also adds an LLM-judged validator
(Haiku) for the soft criteria those layers require.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

Track = Literal["profile", "goals", "needs"]
Layer = Literal["basic", "personality", "identity"]


# ── BASIC layer requirements ────────────────────────────────────────────────
# From `frameworks.md` Depth 1: the factual foundation. The student must
# have enough basic signal that we can place them in a recommendation
# universe. We require five fields. If GPA is missing but a test score is
# present, GPA is satisfied (and vice versa).
BASIC_REQUIRED_FIELDS = {
    "age",
    "education_level",
    "gpa_or_test_score",  # virtual — satisfied by either
    "location_pref",  # any of prefs / avoid being non-empty
    "first_gen",
}

# How much each missing field reduces completion. 5 fields → 20% each.
BASIC_FIELD_WEIGHT = Decimal("0.20")

# Confidence threshold below which an extracted field is treated as
# "not yet known" for state-machine purposes. Calibrated per the extractor
# rules in `prompts/extractor.md`: < 0.7 → caller drops the extraction.
DEFAULT_FIELD_CONFIDENCE_THRESHOLD = Decimal("0.70")


@dataclass
class StudentSnapshot:
    """The known-profile snapshot the validator reasons over.

    Caller (the discovery service) fills this from the StudentProfile row
    plus any artifacts already written for this student. Field values are
    None when not yet known.
    """

    age: int | None = None
    education_level: str | None = None
    gpa: float | None = None
    test_scores: list[dict] = field(default_factory=list)  # [{type, score}]
    location_prefs: list[str] = field(default_factory=list)
    location_avoid: list[str] = field(default_factory=list)
    first_gen: bool | None = None
    income_band: str | None = None
    gender: str | None = None

    @property
    def has_gpa_or_test_score(self) -> bool:
        return self.gpa is not None or len(self.test_scores) > 0

    @property
    def has_location_pref(self) -> bool:
        return bool(self.location_prefs) or bool(self.location_avoid)


@dataclass
class LayerVerdict:
    """The validator's verdict on the current layer.

    `layer_complete` controls whether the orchestrator advances on the next
    turn. `missing_signals` is the gap list the orchestrator is asked to
    probe (one signal per turn — see `next_probe`).
    """

    layer_complete: bool
    completion_pct: Decimal
    missing_signals: list[str] = field(default_factory=list)
    next_probe_hint: str | None = None
    evidence_count: dict[str, int] = field(default_factory=dict)


# ── BASIC layer evaluator ───────────────────────────────────────────────────
# Pure function; no LLM. Invoked by the validator each turn (cheap, deterministic).


def evaluate_basic_layer(snapshot: StudentSnapshot) -> LayerVerdict:
    """Return whether the BASIC layer is complete for this student.

    Completion is the fraction of required fields present (each weighted
    equally). Missing-signal names map to the framework's required fields
    so the orchestrator can pick the next probe naturally.
    """
    missing: list[str] = []

    if snapshot.age is None:
        missing.append("age")
    if snapshot.education_level is None:
        missing.append("education_level")
    if not snapshot.has_gpa_or_test_score:
        missing.append("gpa_or_test_score")
    if not snapshot.has_location_pref:
        missing.append("location_pref")
    if snapshot.first_gen is None:
        missing.append("first_gen")

    fields_present = len(BASIC_REQUIRED_FIELDS) - len(missing)
    completion_pct = BASIC_FIELD_WEIGHT * fields_present if BASIC_REQUIRED_FIELDS else Decimal("0")
    completion_pct = completion_pct.quantize(Decimal("0.001"))

    next_probe_hint = _basic_probe_for_missing(missing)

    return LayerVerdict(
        layer_complete=not missing,
        completion_pct=completion_pct,
        missing_signals=missing,
        next_probe_hint=next_probe_hint,
        evidence_count={f: 1 for f in BASIC_REQUIRED_FIELDS - set(missing)},
    )


def _basic_probe_for_missing(missing: list[str]) -> str | None:
    """Pick the most natural follow-up question for the first missing field.

    The orchestrator is asked to deliver this as a probe; it may rephrase
    but must not change intent. Order matters — earlier fields have more
    rapport-building weight than later ones.
    """
    if not missing:
        return None

    # Prefer fields that flow naturally early in a conversation.
    priority = [
        "education_level",
        "age",
        "location_pref",
        "first_gen",
        "gpa_or_test_score",
    ]
    for field_name in priority:
        if field_name in missing:
            return _PROBE_TEMPLATES[field_name]
    return None


_PROBE_TEMPLATES: dict[str, str] = {
    "age": (
        "How old are you, roughly? I'm asking because age shapes which programs "
        "make sense — undergrad versus grad versus accelerated paths."
    ),
    "education_level": (
        "Where are you in your education right now? Senior in high school, "
        "partway through college, working, or somewhere in between?"
    ),
    "gpa_or_test_score": (
        "What's your most recent academic signal — GPA, or a test score like "
        "the SAT/GRE/TOEFL — whichever feels more representative?"
    ),
    "location_pref": (
        "Where in the world are you open to studying — and is there anywhere you'd rule out?"
    ),
    "first_gen": (
        "Did either of your parents attend college? It changes which support "
        "structures matter for you and what financial-aid paths are open."
    ),
}


# ── Track-level completion (used for session.completion_pct) ────────────────


def basic_layer_completion(snapshot: StudentSnapshot) -> Decimal:
    """Convenience — returns just the % so the service layer can update
    session.completion_pct without unpacking a full verdict."""
    return evaluate_basic_layer(snapshot).completion_pct
