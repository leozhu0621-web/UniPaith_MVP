"""Phase B1 — ML matcher.

Pure-Python; no LLM. Takes a student's emitted features (sparse + dense
embedding) and a program's features (same shape, computed offline) and
returns (fitness_score, confidence_score) with explainable component
breakdowns.

Scoring layers (in order)
-------------------------
1. **Hard filters (rule layer)** — eliminate ineligible programs.
   `education_level` mismatch, geo on the avoid list, deadline horizon,
   etc. Eliminated programs return fitness=0, confidence=1, eliminated=True.
2. **Content cosine** — voyage-3-large 1024-d cosine on the applicant
   summary embedding ↔ program description embedding. 0.45 weight.
3. **Soft alignment** — interest/career/value tag overlap (Jaccard
   variant) + social_prefs alignment. 0.35 weight.
4. **Needs match** — needs_signals overlap weighted by severity. 0.20
   weight.

Confidence math
---------------
Confidence is **not** a recalibration of fitness — it answers "how well
do we actually know this student/program pair." Computed as the
geometric mean of four [0,1] terms:
- profile_completeness   (from feature_completeness)
- extractor_quality      (from upstream confidence — placeholder 0.85
                          in cold start until we wire turn-level data)
- program_data_quality   (from program.data_completeness)
- distance_to_training   (1.0 in cold start; tightens once we have
                          enough labeled data to fit a calibrator)

The geometric mean (rather than arithmetic) penalizes any single low
term — if program data is sparse, confidence drops to reflect that
even if the student is fully known.

Two scores, two stories
-----------------------
- High fitness, low confidence → "we think this fits, but we don't know
  enough about you yet to be sure."
- Low fitness, high confidence → "this is clearly not for you."
- These are surfaced separately in the UI; the matcher never collapses
  them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

# ── Default weights ─────────────────────────────────────────────────────────
# Hand-tuned for cold start. Phase B1 exit gate: NDCG@10 ≥ 0.65 against
# 100 internally-rated (student, program) pairs. If NDCG misses, the
# tuning lever is here — three numbers that must sum to 1.0.

DEFAULT_WEIGHTS = {
    "cosine": 0.45,
    "soft_align": 0.35,
    "needs_match": 0.20,
}


@dataclass
class StudentFeatures:
    """The matcher's view of a student. Built from
    `student_feature_vectors.sparse_features` + `embedding`.
    """

    sparse: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    profile_completeness: float = 0.0
    extractor_quality: float = 0.85  # placeholder; see module docstring


@dataclass
class ProgramFeatures:
    """The matcher's view of a program. Same vocabulary as the student
    side, computed offline by `unipaith.services.program_features`.
    """

    program_id: Any  # uuid.UUID at runtime; left untyped to avoid hard import
    sparse: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    data_completeness: float = 0.5  # cold-start default


@dataclass
class Score:
    """One scored (student, program) pair."""

    fitness: Decimal = Decimal("0")
    confidence: Decimal = Decimal("0")
    eliminated: bool = False
    fitness_breakdown: dict[str, Any] = field(default_factory=dict)
    confidence_breakdown: dict[str, Any] = field(default_factory=dict)


# ── Hard-filter rule layer ──────────────────────────────────────────────────


def rule_pass(student: StudentFeatures, program: ProgramFeatures) -> tuple[bool, str | None]:
    """Apply hard filters. Returns (passed, reason_if_eliminated).

    Reasons are returned for the rationale agent (later phase) to
    explain why a program was filtered out — UI can choose to show
    these or hide eliminated programs entirely.
    """
    # Education-level compatibility. Examples:
    #   high_school → bachelor's programs only
    #   bachelors   → masters / PhD / professional
    s_lvl = student.sparse.get("education_level")
    p_target = program.sparse.get("target_education_level")  # what level the
    # program *wants* applicants from. None means any.
    if p_target and s_lvl and s_lvl != "unknown":
        compat = _education_compat(s_lvl, p_target)
        if not compat:
            return False, f"education_mismatch:{s_lvl}→{p_target}"

    # Geo must — student requires location must be in program's locations.
    # Empty geo_must means flexible.
    s_must = set(student.sparse.get("geo_must") or [])
    p_locs = set(program.sparse.get("locations") or [])
    if s_must and p_locs and not (s_must & p_locs):
        return False, f"geo_must_disjoint:{s_must}∩{p_locs}=∅"

    # Geo avoid — program's locations include something the student avoids.
    s_avoid = set(student.sparse.get("geo_avoid") or [])
    if s_avoid and p_locs and (s_avoid & p_locs) == p_locs:
        # All of the program's locations are on the student's avoid list.
        return False, f"geo_avoid:{s_avoid & p_locs}"

    # Budget. Student's max_usd_per_year < program's tuition.
    s_budget = student.sparse.get("budget_max_usd_per_year")
    p_tuition = program.sparse.get("tuition_usd_per_year")
    if (
        s_budget is not None
        and p_tuition is not None
        and not student.sparse.get("needs_aid", False)
        and p_tuition > s_budget
    ):
        return False, f"budget:{p_tuition}>{s_budget}"

    return True, None


def _education_compat(student_level: str, program_target: str) -> bool:
    """Is a student at `student_level` an eligible applicant to a program
    that targets `program_target`?

    Compatibility table (stays explicit so reviewers can audit it):
        high_school   → bachelors
        bachelors     → masters | doctoral | professional
        masters       → masters | doctoral | professional
        gap_year      → bachelors
        working       → masters | doctoral | professional
    """
    table: dict[str, set[str]] = {
        "high_school": {"bachelors"},
        "bachelors": {"masters", "doctoral", "professional"},
        "masters": {"masters", "doctoral", "professional"},
        "gap_year": {"bachelors"},
        "working": {"masters", "doctoral", "professional"},
    }
    allowed = table.get(student_level, set())
    return program_target in allowed


# ── Component scorers ──────────────────────────────────────────────────────


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    """Cosine similarity in [-1, 1]; clamps to [0, 1] for the fitness layer
    (negative cosine on free-text summaries is rare and not actionable)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def soft_align(student: StudentFeatures, program: ProgramFeatures) -> float:
    """Tag-overlap score in [0,1]. Weighted average of three sub-scores:
    interest themes (0.4), career arcs (0.4), values (0.2). Each
    sub-score is Jaccard-with-floor: |A∩B| / max(1, |A∪B|).

    Plus social_prefs alignment: dot-product of the student's [0,1]
    preference vector against the program's [0,1] feature vector,
    normalized by length.
    """
    s = student.sparse
    p = program.sparse

    interest_score = _jaccard(s.get("interest_themes") or [], p.get("interest_themes") or [])
    career_score = _jaccard(s.get("career_arcs") or [], p.get("career_arcs") or [])
    value_score = _jaccard(s.get("values") or [], p.get("values") or [])

    tag_score = 0.4 * interest_score + 0.4 * career_score + 0.2 * value_score

    social_score = _vec_align(
        s.get("social_prefs") or {}, p.get("social_features") or {}
    )

    # 70/30 split: tag overlap dominates; social prefs polish the result.
    return 0.7 * tag_score + 0.3 * social_score


def needs_match(student: StudentFeatures, program: ProgramFeatures) -> float:
    """How well the program's `support_signals` cover the student's
    `needs_signals` weighted by severity.

    For each needs_signal the student carries (with severity in [0,1]):
      - if the program has the matching support_signal at strength s_p
        in [0,1], contribute severity * s_p.
      - otherwise contribute 0.
    Normalized by the sum of student severities.
    """
    s_needs: dict[str, float] = student.sparse.get("needs_signals") or {}
    p_supports: dict[str, float] = program.sparse.get("support_signals") or {}
    if not s_needs:
        return 0.5  # no needs expressed → neutral; don't punish the program
    total_weight = sum(max(0.0, min(1.0, sev)) for sev in s_needs.values())
    if total_weight == 0:
        return 0.5
    matched = 0.0
    for tag, severity in s_needs.items():
        sev = max(0.0, min(1.0, severity))
        program_strength = max(0.0, min(1.0, float(p_supports.get(tag, 0.0))))
        matched += sev * program_strength
    return matched / total_weight


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / max(1, len(sa | sb))


def _vec_align(a: dict[str, float], b: dict[str, float]) -> float:
    """Aligned-key dot product for two [0,1]-valued sparse vectors,
    normalized so identical vectors return 1.0 and disjoint return 0.0.
    """
    keys = set(a.keys()) | set(b.keys())
    if not keys:
        return 0.0
    dot = sum(
        max(0.0, min(1.0, a.get(k, 0.0))) * max(0.0, min(1.0, b.get(k, 0.0)))
        for k in keys
    )
    return min(1.0, dot / len(keys))


# ── Top-level scoring ──────────────────────────────────────────────────────


def score(
    student: StudentFeatures,
    program: ProgramFeatures,
    *,
    weights: dict[str, float] | None = None,
) -> Score:
    """Return a fully-explainable Score for one (student, program) pair."""
    weights = weights or DEFAULT_WEIGHTS
    rp, reason = rule_pass(student, program)
    if not rp:
        return Score(
            fitness=Decimal("0.0000"),
            confidence=Decimal("1.0000"),
            eliminated=True,
            fitness_breakdown={"eliminated": True, "reason": reason},
            confidence_breakdown={"eliminated": True},
        )

    cos_score = cosine(student.embedding, program.embedding)
    soft_score = soft_align(student, program)
    needs_score = needs_match(student, program)

    fitness = (
        weights["cosine"] * cos_score
        + weights["soft_align"] * soft_score
        + weights["needs_match"] * needs_score
    )
    fitness = max(0.0, min(1.0, fitness))

    # Confidence: geometric mean of four terms.
    profile = max(0.0, min(1.0, student.profile_completeness))
    extractor = max(0.0, min(1.0, student.extractor_quality))
    program_q = max(0.0, min(1.0, program.data_completeness))
    extrapolation = 1.0  # cold-start placeholder (see module docstring)
    # Geometric mean. If any term is 0, confidence is 0 — which is
    # exactly what we want (a single zeroed component should kill it).
    confidence = (profile * extractor * program_q * extrapolation) ** 0.25

    return Score(
        fitness=Decimal(str(round(fitness, 4))),
        confidence=Decimal(str(round(confidence, 4))),
        eliminated=False,
        fitness_breakdown={
            "cosine": round(cos_score, 4),
            "soft_align": round(soft_score, 4),
            "needs_match": round(needs_score, 4),
            "weights": weights,
        },
        confidence_breakdown={
            "profile_completeness": round(profile, 4),
            "extractor_quality": round(extractor, 4),
            "program_data_quality": round(program_q, 4),
            "extrapolation": round(extrapolation, 4),
        },
    )


def rank_programs(
    student: StudentFeatures,
    programs: list[ProgramFeatures],
    *,
    weights: dict[str, float] | None = None,
    include_eliminated: bool = False,
) -> list[tuple[ProgramFeatures, Score]]:
    """Score every program and return them sorted by fitness desc.

    `include_eliminated`: if True, eliminated programs are returned at
    the bottom of the list with fitness=0 (useful for the rationale
    agent, which may explain why something was filtered).
    """
    scored = [(p, score(student, p, weights=weights)) for p in programs]
    if not include_eliminated:
        scored = [(p, s) for p, s in scored if not s.eliminated]
    scored.sort(key=lambda ps: (float(ps[1].fitness), float(ps[1].confidence)), reverse=True)
    return scored
