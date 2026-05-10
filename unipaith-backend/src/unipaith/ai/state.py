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
class PersonalityEntry:
    """One personality-layer signal with provenance."""

    facet: str  # see PERSONALITY_FACETS
    value: str
    evidence: str  # verbatim student quote


@dataclass
class IdentityClaim:
    """One identity-layer claim with verbatim evidence and confirmation status."""

    facet: str  # 'value' | 'belief' | 'view' | 'self_awareness'
    claim: str
    evidence: str
    user_confirmed: bool = False


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
    # PERSONALITY + IDENTITY layers (Phase A3)
    personality: list[PersonalityEntry] = field(default_factory=list)
    identity_claims: list[IdentityClaim] = field(default_factory=list)

    @property
    def has_gpa_or_test_score(self) -> bool:
        return self.gpa is not None or len(self.test_scores) > 0

    @property
    def has_location_pref(self) -> bool:
        return bool(self.location_prefs) or bool(self.location_avoid)

    def personality_facets_with_evidence(self) -> set[str]:
        """Distinct personality facets backed by non-empty evidence."""
        return {p.facet for p in self.personality if p.evidence and p.value}

    def identity_value_or_belief_count(self) -> int:
        """Distinct (claim, evidence) pairs in {value, belief, view}."""
        seen: set[tuple[str, str]] = set()
        for c in self.identity_claims:
            if c.facet in {"value", "belief", "view"}:
                seen.add((c.claim.strip().lower()[:120], c.evidence.strip().lower()[:120]))
        return len(seen)

    def has_self_awareness_moment(self) -> bool:
        return any(c.facet == "self_awareness" and c.evidence for c in self.identity_claims)

    def confirmed_identity_claims(self) -> int:
        return sum(1 for c in self.identity_claims if c.user_confirmed)


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


# ── PERSONALITY layer evaluator ─────────────────────────────────────────────
# Per `frameworks.md` Depth 2: ≥4 of the 7 facets, each with an evidence
# quote. The evaluator is deterministic (count-based); the LLM-as-judge in
# `validator.py` rates the *quality* of each entry's evidence.

PERSONALITY_FACETS = {
    "interest",
    "passion",
    "career_direction",
    "peer_style",
    "conflict_style",
    "location_emotional",
    "connection_style",
}

PERSONALITY_REQUIRED_FACETS = 4
PERSONALITY_FACET_WEIGHT = Decimal("0.25")  # 4 facets × 25% = 100%


def evaluate_personality_layer(snapshot: StudentSnapshot) -> LayerVerdict:
    """Return whether the PERSONALITY layer is complete.

    Frameworks rule: ≥4 facets present, each with a verbatim evidence
    quote. Completion is `present_facets / required_facets`, capped at 1.0.
    """
    present = snapshot.personality_facets_with_evidence()
    fraction = min(len(present), PERSONALITY_REQUIRED_FACETS) / PERSONALITY_REQUIRED_FACETS
    completion = Decimal(str(round(fraction, 3)))

    missing_signal_names: list[str] = []
    if len(present) < PERSONALITY_REQUIRED_FACETS:
        # Show which facets are still empty so the orchestrator can pick a
        # natural follow-up. Order matches conversation-flow priority.
        for facet in (
            "career_direction",
            "interest",
            "peer_style",
            "connection_style",
            "passion",
            "location_emotional",
            "conflict_style",
        ):
            if facet not in present:
                missing_signal_names.append(f"personality.{facet}")
            if len(missing_signal_names) >= PERSONALITY_REQUIRED_FACETS - len(present):
                break

    next_probe = _personality_probe_for_missing(missing_signal_names)

    return LayerVerdict(
        layer_complete=len(present) >= PERSONALITY_REQUIRED_FACETS,
        completion_pct=completion,
        missing_signals=missing_signal_names,
        next_probe_hint=next_probe,
        evidence_count={f"personality.{f}": 1 for f in present},
    )


def _personality_probe_for_missing(missing: list[str]) -> str | None:
    if not missing:
        return None
    facet = missing[0].split(".", 1)[1]
    return _PERSONALITY_PROBE_TEMPLATES.get(facet)


_PERSONALITY_PROBE_TEMPLATES: dict[str, str] = {
    "career_direction": (
        "When you imagine yourself five years out — not the title, but the "
        "*shape* of the work — what does it look like?"
    ),
    "interest": (
        "Tell me about a project or topic last year that you couldn't put "
        "down. What kept pulling you back?"
    ),
    "peer_style": (
        "Do you do your best work in a small intense group, or in a big "
        "lively community? Tell me which one drains you and which one fills "
        "you up."
    ),
    "connection_style": (
        "Who do you learn most from — a single mentor, a tight peer group, "
        "or mostly working through things alone?"
    ),
    "passion": (
        "What's something you'd still do even if no one ever asked you to "
        "or paid you for it?"
    ),
    "location_emotional": (
        "Beyond the practical stuff — what does the *feel* of a place mean "
        "to you? Urban energy, quiet corners, weather, distance from home?"
    ),
    "conflict_style": (
        "When a class debate gets sharp — or a project disagreement gets "
        "hot — what's your move? Lean in, mediate, step back?"
    ),
}


# ── IDENTITY layer evaluator ────────────────────────────────────────────────
# Per `frameworks.md` Depth 3: ≥3 distinct value/belief claims AND
# ≥1 self-awareness moment AND the student has explicitly confirmed at
# least 2 of these claims (not just nodded along).
#
# Three exit conditions, gated independently. Completion percentage is the
# minimum of the three sub-percentages (the layer is only as strong as its
# weakest condition).

IDENTITY_REQUIRED_VALUE_BELIEFS = 3
IDENTITY_REQUIRED_SELF_AWARENESS = 1
IDENTITY_REQUIRED_CONFIRMATIONS = 2


def evaluate_identity_layer(snapshot: StudentSnapshot) -> LayerVerdict:
    """Return whether the IDENTITY layer is complete.

    Three independent gates. Layer-complete only when all three are met.
    """
    vb_count = snapshot.identity_value_or_belief_count()
    has_sa = snapshot.has_self_awareness_moment()
    confirmed = snapshot.confirmed_identity_claims()

    vb_pct = min(vb_count, IDENTITY_REQUIRED_VALUE_BELIEFS) / IDENTITY_REQUIRED_VALUE_BELIEFS
    sa_pct = 1.0 if has_sa else 0.0
    cf_pct = min(confirmed, IDENTITY_REQUIRED_CONFIRMATIONS) / IDENTITY_REQUIRED_CONFIRMATIONS

    completion = Decimal(str(round(min(vb_pct, sa_pct, cf_pct), 3)))

    missing: list[str] = []
    if vb_count < IDENTITY_REQUIRED_VALUE_BELIEFS:
        missing.append(
            f"identity.value_or_belief ({vb_count}/{IDENTITY_REQUIRED_VALUE_BELIEFS})"
        )
    if not has_sa:
        missing.append("identity.self_awareness_moment")
    if confirmed < IDENTITY_REQUIRED_CONFIRMATIONS:
        missing.append(
            f"identity.user_confirmation ({confirmed}/{IDENTITY_REQUIRED_CONFIRMATIONS})"
        )

    next_probe = _identity_probe_for_missing(missing)

    return LayerVerdict(
        layer_complete=not missing,
        completion_pct=completion,
        missing_signals=missing,
        next_probe_hint=next_probe,
        evidence_count={
            "identity.value_or_belief": vb_count,
            "identity.self_awareness": int(has_sa),
            "identity.confirmed": confirmed,
        },
    )


def _identity_probe_for_missing(missing: list[str]) -> str | None:
    if not missing:
        return None
    first = missing[0]
    if first.startswith("identity.value_or_belief"):
        return _IDENTITY_PROBES["value_or_belief"]
    if first == "identity.self_awareness_moment":
        return _IDENTITY_PROBES["self_awareness"]
    if first.startswith("identity.user_confirmation"):
        return _IDENTITY_PROBES["confirmation"]
    return None


_IDENTITY_PROBES: dict[str, str] = {
    "value_or_belief": (
        "What's a belief you hold about how the world works — or about "
        "what matters — that you'd defend even if it cost you something?"
    ),
    "self_awareness": (
        "Tell me about a time you noticed you were wrong about yourself — "
        "or saw a pattern in your own behavior that surprised you."
    ),
    "confirmation": (
        "I want to read back a couple of things you've told me to make sure "
        "I'm hearing you right. Does this still ring true to you, or has it "
        "shifted as we've talked?"
    ),
}
