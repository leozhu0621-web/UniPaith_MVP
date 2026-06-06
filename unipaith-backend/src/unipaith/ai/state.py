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

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

# "discovery" = the unified, track-less Uni conversation (one session covers
# self/goals/needs by content). "profile"/"goals"/"needs" remain for legacy
# sessions + per-signal validators.
Track = Literal["profile", "goals", "needs", "discovery"]
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
class GoalEntry:
    """One SMART goal with provenance and completeness tracking.

    `completeness` (0–1) reflects how many of the five SMART fields are
    populated. Only goals with completeness == 1.0 are committed to
    `student_goals`; partials live in the audit trail until probed.
    """

    category: str  # 'academic' | 'social' | 'personal'
    specific: str
    measurable: str | None = None
    achievable: str | None = None
    relevant: str | None = None
    time_bound: str | None = None
    completeness: float = 0.0
    user_confirmed: bool = False


@dataclass
class NeedEntry:
    """One Maslow-tagged need signal."""

    # 'physiological' | 'safety' | 'social' | 'self_esteem' | 'self_actualization'
    maslow_level: str
    signal: str  # controlled-vocab tag
    free_text: str = ""
    severity: int | None = None  # 1–5
    evidence: str = ""
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
    # GOALS + NEEDS tracks (Phase A3.2)
    goals: list[GoalEntry] = field(default_factory=list)
    needs: list[NeedEntry] = field(default_factory=list)

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

    # GOALS helpers ─────────────────────────────────────────────────────
    def goals_by_category(self) -> dict[str, list[GoalEntry]]:
        out: dict[str, list[GoalEntry]] = {}
        for g in self.goals:
            out.setdefault(g.category, []).append(g)
        return out

    def complete_goal_categories(self) -> set[str]:
        """Categories with at least one fully-completed (SMART-filled),
        user-confirmed goal."""
        return {
            g.category
            for g in self.goals
            if g.completeness >= 1.0 and g.user_confirmed and g.specific
        }

    # NEEDS helpers ──────────────────────────────────────────────────────
    def needs_by_level(self) -> dict[str, list[NeedEntry]]:
        out: dict[str, list[NeedEntry]] = {}
        for n in self.needs:
            out.setdefault(n.maslow_level, []).append(n)
        return out

    def covered_maslow_levels(self) -> set[str]:
        """Maslow levels with ≥1 signal (any severity, any confirmation)."""
        return {n.maslow_level for n in self.needs if n.signal}


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
        "What's something you'd still do even if no one ever asked you to or paid you for it?"
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
        missing.append(f"identity.value_or_belief ({vb_count}/{IDENTITY_REQUIRED_VALUE_BELIEFS})")
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


# ── GOALS track evaluator ──────────────────────────────────────────────────
# Per `frameworks.md`: at least one goal in each of {academic, social,
# personal}, all five SMART fields filled, user-confirmed. Three independent
# category gates — completion is the fraction of categories with ≥1
# qualifying goal.

GOAL_CATEGORIES = {"academic", "social", "personal"}


def evaluate_goals_track(snapshot: StudentSnapshot) -> LayerVerdict:
    """Return whether the GOALS track is complete.

    Required: ≥1 fully-SMART, user-confirmed goal in each of academic /
    social / personal. Completion = fraction of categories satisfied.
    """
    complete_cats = snapshot.complete_goal_categories()
    missing_cats = sorted(GOAL_CATEGORIES - complete_cats)

    completion = Decimal(str(round(len(complete_cats) / len(GOAL_CATEGORIES), 3)))
    next_probe = _goals_probe_for_missing(missing_cats, snapshot)

    return LayerVerdict(
        layer_complete=not missing_cats,
        completion_pct=completion,
        missing_signals=[f"goals.{c}" for c in missing_cats],
        next_probe_hint=next_probe,
        evidence_count={f"goals.{c}": 1 for c in complete_cats},
    )


def _goals_probe_for_missing(missing_cats: list[str], snapshot: StudentSnapshot) -> str | None:
    """Probe for the first missing category. If a partial goal already
    exists in that category, ask for the specific missing SMART field
    rather than restarting."""
    if not missing_cats:
        return None
    first_cat = missing_cats[0]
    by_cat = snapshot.goals_by_category()
    drafts = by_cat.get(first_cat, [])
    if drafts:
        # Find the most-complete draft and ask for its first missing field.
        best = max(drafts, key=lambda g: g.completeness)
        if not best.measurable:
            return _GOALS_FIELD_PROBES["measurable"](best)
        if not best.time_bound:
            return _GOALS_FIELD_PROBES["time_bound"](best)
        if not best.achievable:
            return _GOALS_FIELD_PROBES["achievable"](best)
        if not best.relevant:
            return _GOALS_FIELD_PROBES["relevant"](best)
        if not best.user_confirmed:
            return _GOALS_FIELD_PROBES["confirm"](best)
    return _GOALS_CATEGORY_OPENERS[first_cat]


_GOALS_CATEGORY_OPENERS: dict[str, str] = {
    "academic": (
        "Now let's set an academic goal. What's one thing you want to have "
        "achieved by the end of your program — degree, paper, qualification, "
        "anything specific?"
    ),
    "social": (
        "What's a social goal — connection, community, networking — that "
        "would make this whole journey feel worth it to you?"
    ),
    "personal": (
        "Outside academics and people — finance, wellbeing, family, time "
        "horizon — what's a personal goal you're holding?"
    ),
}


def _probe_measurable(g: GoalEntry) -> str:
    return f"How would you know you hit '{g.specific[:80]}'? What's the measurable signal?"


def _probe_time_bound(g: GoalEntry) -> str:
    return f"By when do you want '{g.specific[:80]}' done?"


def _probe_achievable(g: GoalEntry) -> str:
    return f"What makes '{g.specific[:80]}' within reach for you — not what makes it easy?"


def _probe_relevant(g: GoalEntry) -> str:
    return (
        f"How does '{g.specific[:80]}' connect to who you are or what "
        "you've already told me you care about?"
    )


def _probe_confirm(g: GoalEntry) -> str:
    return (
        f"I have this goal in your stack: '{g.specific[:120]}'. Does that "
        "still feel right, or has it shifted?"
    )


_GOALS_FIELD_PROBES: dict[str, Callable[[GoalEntry], str]] = {
    "measurable": _probe_measurable,
    "time_bound": _probe_time_bound,
    "achievable": _probe_achievable,
    "relevant": _probe_relevant,
    "confirm": _probe_confirm,
}


def goals_track_completion(snapshot: StudentSnapshot) -> Decimal:
    """Convenience — return just the completion %."""
    return evaluate_goals_track(snapshot).completion_pct


# ── NEEDS track evaluator ──────────────────────────────────────────────────
# Per `frameworks.md`: at least one signal at EACH of physiological, safety,
# social, self_esteem, self_actualization — OR an explicit "N/A" with
# reason. Five independent level gates; completion is fraction covered.

MASLOW_LEVELS = (
    "physiological",
    "safety",
    "social",
    "self_esteem",
    "self_actualization",
)


def evaluate_needs_track(snapshot: StudentSnapshot) -> LayerVerdict:
    """Return whether the NEEDS track is complete.

    Required: ≥1 signal at each of the 5 Maslow levels (or explicit N/A
    via the `n_a` signal tag).
    """
    covered = snapshot.covered_maslow_levels()
    missing_levels = [lv for lv in MASLOW_LEVELS if lv not in covered]

    completion = Decimal(str(round(len(covered) / len(MASLOW_LEVELS), 3)))
    next_probe = _needs_probe_for_missing(missing_levels)

    return LayerVerdict(
        layer_complete=not missing_levels,
        completion_pct=completion,
        missing_signals=[f"needs.{lv}" for lv in missing_levels],
        next_probe_hint=next_probe,
        evidence_count={f"needs.{lv}": 1 for lv in covered},
    )


def _needs_probe_for_missing(missing: list[str]) -> str | None:
    if not missing:
        return None
    return _NEEDS_PROBES.get(missing[0])


_NEEDS_PROBES: dict[str, str] = {
    "physiological": (
        "Let's talk about the basics. What's non-negotiable about the "
        "physical environment of where you study — housing, food, climate, "
        "anything you can't compromise on?"
    ),
    "safety": (
        "What about safety in the broader sense — healthcare access, "
        "financial stability, immigration status, the policy environment "
        "of where you'd live?"
    ),
    "social": (
        "Who do you want to walk into class with? Tell me about the "
        "community, culture, or peer atmosphere that would matter to you."
    ),
    "self_esteem": (
        "What's the kind of recognition or environment that would make "
        "you feel seen and valued — scholarships, peer respect, a brand "
        "your family would understand?"
    ),
    "self_actualization": (
        "Last layer — the highest-level stuff. Events, alumni networks, "
        "research, study-abroad, mental-health support, the aspirations "
        "you hold quietly. What's on that list for you?"
    ),
}


def needs_track_completion(snapshot: StudentSnapshot) -> Decimal:
    """Convenience — return just the completion %."""
    return evaluate_needs_track(snapshot).completion_pct
