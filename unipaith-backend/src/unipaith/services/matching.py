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

The three weights are a convex combination over the components we can
actually evaluate for a given pair. When an embedding is missing on either
side (the cold-start default until the embedding pipeline is wired), the
cosine term is dropped and its weight is **redistributed** across soft
alignment and needs match — fitness stays a true [0, 1] score instead of
being silently capped at 0.55. See `_renormalized_weights`.

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

from .match import fits as _fits
from .match.params import DEFAULT_PARAMS, clamp01, confidence_to_gain, two_sided_confidence

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

    social_score = _vec_align(s.get("social_prefs") or {}, p.get("social_features") or {})

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
    dot = sum(max(0.0, min(1.0, a.get(k, 0.0))) * max(0.0, min(1.0, b.get(k, 0.0))) for k in keys)
    return min(1.0, dot / len(keys))


# ── Top-level scoring ──────────────────────────────────────────────────────


def _renormalized_weights(
    weights: dict[str, float], available: dict[str, float]
) -> dict[str, float]:
    """Restrict ``weights`` to the components actually computable for a
    given (student, program) pair and renormalize them to sum to 1.0.

    A component the matcher can't evaluate — chiefly ``cosine`` when either
    side has no embedding — must NOT silently contribute 0 to the weighted
    fitness sum. Doing so penalizes every program by that component's whole
    weight: with the default budget, an absent embedding alone caps
    achievable fitness at 0.55 (0.35 soft + 0.20 needs), so even a perfect
    tag/needs match reads as "55% fit". Redistributing the missing weight
    across the present components keeps fitness a true [0, 1] convex
    combination of what we can actually measure. When every component is
    available (and the weights already sum to 1.0) this is a no-op.
    """
    active = {k: float(weights[k]) for k in available if k in weights}
    total = sum(active.values())
    if total <= 0 or abs(total - 1.0) < 1e-9:
        # Already a convex combination over the present components — leave the
        # values untouched so the common all-components-available path is an
        # exact no-op (no float drift on the persisted breakdown weights).
        return active
    return {k: v / total for k, v in active.items()}


# ── CPEF — Coverage-damped Posterior Expected-Fit (Spec 3, AI Structure) ─────
# One fused fit+confidence number per (student, program), with an in-formula
# deal-breaker veto and a coverage damp — no separate hard filter, no separate
# confidence ring. Gated by `settings.cpef_matching_enabled`; the legacy
# convex-sum path below stays the default fallback until CPEF proves out.
#
# Slice A note: per-signal confidence is uniform (real per-signal confidence
# is fed by Spec 1 enrichment + Spec 2 authority precedence in later slices).
# So today CPEF is a confidence-light, typed-fit, coverage-damped, vetoed
# weighted average — already richer than the cosine/soft/needs convex sum.

_CPEF_CONF = 0.95  # placeholder per-signal confidence (each side) for Slice A
_CANONICAL_N = 5  # fit dimensions used for the coverage denominator


def _coverage(present_a_sum: float, full_w_sum: float, n0: float) -> float:
    denom = n0 + full_w_sum
    if denom <= 0:
        return 1.0
    return clamp01((n0 + present_a_sum) / denom)


def _build_cpef_signals(
    student: StudentFeatures, program: ProgramFeatures, p: dict[str, float]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    """Assemble the per-signal fit list + deal-breakers from the projected
    sparse features that exist today. Returns (signals, dealbreakers, full_w)."""
    s, pr = student.sparse, program.sparse
    prior = p["prior"]
    w_base = p["w_base"]
    c = two_sided_confidence(_CPEF_CONF, _CPEF_CONF)
    rho = confidence_to_gain(c, p)
    signals: list[dict[str, Any]] = []

    # semantic (embedding cosine), only when both sides have a matching vector
    if student.embedding and program.embedding and len(student.embedding) == len(program.embedding):
        signals.append(
            {
                "key": "semantic",
                "f": cosine(student.embedding, program.embedding),
                "c": c,
                "w": w_base,
                "prior": prior,
            }
        )
    # themes (interest/career/value tag overlap) — always defined via fallbacks
    signals.append(
        {"key": "themes", "f": soft_align(student, program), "c": c, "w": w_base, "prior": prior}
    )
    # needs coverage — neutral 0.5 when the student expressed no needs
    signals.append(
        {"key": "needs", "f": needs_match(student, program), "c": c, "w": w_base, "prior": prior}
    )

    # budget — graded affordability (a *fit*, distinct from the over-budget veto)
    s_budget = s.get("budget_max_usd_per_year")
    p_tuition = pr.get("tuition_usd_per_year")
    if s_budget is not None and p_tuition is not None and not s.get("needs_aid", False):
        signals.append(
            {
                "key": "budget",
                "f": _fits.fit_range(float(p_tuition), float(s_budget), p["delta"]),
                "c": c,
                "w": w_base,
                "prior": prior,
            }
        )
    # geo — overlap of preferred vs program locations
    s_geo = s.get("geo_must") or []
    p_locs = pr.get("locations") or []
    if s_geo and p_locs:
        signals.append(
            {"key": "geo", "f": _fits.fit_geo(s_geo, p_locs), "c": c, "w": w_base, "prior": prior}
        )

    # ── deal-breakers (in-formula veto, not a pre-filter) ──
    dealbreakers: list[dict[str, Any]] = []
    s_lvl = s.get("education_level")
    p_target = pr.get("target_education_level")
    if p_target and s_lvl and s_lvl != "unknown":
        ok = _education_compat(s_lvl, p_target)
        dealbreakers.append({"key": "degree", "v": (1.0 if ok else p["epsilon"]), "rho": rho})
    if s_budget is not None and p_tuition is not None and not s.get("needs_aid", False):
        ceiling = float(s_budget) * (1.0 + p["delta"])
        if float(p_tuition) > ceiling:
            span = max(1e-9, float(s_budget) * p["delta"])
            v = max(p["epsilon"], clamp01(1.0 - (float(p_tuition) - ceiling) / span))
            dealbreakers.append({"key": "budget", "v": v, "rho": rho})
    s_avoid = set(s.get("geo_avoid") or [])
    if s_avoid and p_locs and (s_avoid & set(p_locs)) == set(p_locs):
        dealbreakers.append({"key": "geo_avoid", "v": p["epsilon"], "rho": rho})

    full_w = _CANONICAL_N * (w_base / 10.0)
    return signals, dealbreakers, full_w


def cpef(
    student: StudentFeatures, program: ProgramFeatures, *, params: dict[str, float] | None = None
) -> tuple[float, dict[str, Any]]:
    """Compute the one CPEF number (student→program direction) + breakdown."""
    p = params or DEFAULT_PARAMS
    signals, dealbreakers, full_w = _build_cpef_signals(student, program, p)

    num = den = present_a = rho_sum = 0.0
    sig_bd: list[dict[str, Any]] = []
    for sig in signals:
        rho = confidence_to_gain(sig["c"], p)
        fhat = sig["f"] * rho + (1.0 - rho) * sig["prior"]
        a = (sig["w"] / 10.0) * rho
        num += a * fhat
        den += a
        present_a += a
        rho_sum += rho
        sig_bd.append(
            {
                "key": sig["key"],
                "f": round(sig["f"], 4),
                "rho": round(rho, 4),
                "fhat": round(fhat, 4),
                "a": round(a, 4),
            }
        )
    inner = (num / den) if den > 0 else p["prior"]

    v_total = 1.0
    hard = False
    db_bd: list[dict[str, Any]] = []
    for db in dealbreakers:
        v_eff = 1.0 - db["rho"] * (1.0 - db["v"])
        v_total *= v_eff
        if db["rho"] >= p["confirmed_gain"] and db["v"] <= p["epsilon"]:
            hard = True
        db_bd.append({"key": db["key"], "v": round(db["v"], 4), "v_eff": round(v_eff, 4)})

    g = _coverage(present_a, full_w, p["n0"])
    value = clamp01(g * v_total * inner)
    if hard:
        # A confirmed true deal-breaker sinks below every clean (un-vetoed) program.
        value = min(value, p["epsilon"] * inner)
    mean_rho = (rho_sum / len(signals)) if signals else 0.0

    breakdown = {
        "model": "cpef",
        "value": round(value, 4),
        "inner": round(inner, 4),
        "coverage": round(g, 4),
        "veto": round(v_total, 4),
        "hard_floor": hard,
        "mean_rho": round(mean_rho, 4),
        "signals": sig_bd,
        "dealbreakers": db_bd,
    }
    return value, breakdown


def _cpef_flag() -> bool:
    try:
        from unipaith.config import settings

        return bool(getattr(settings, "cpef_matching_enabled", False))
    except Exception:
        return False


def _score_cpef(
    student: StudentFeatures, program: ProgramFeatures, *, params: dict[str, float] | None = None
) -> Score:
    value, bd = cpef(student, program, params=params)
    conf = bd["mean_rho"]
    return Score(
        fitness=Decimal(str(round(value, 4))),
        confidence=Decimal(str(round(conf, 4))),
        eliminated=False,  # nothing is hard-dropped; vetoed programs sink instead
        fitness_breakdown=bd,
        confidence_breakdown={"mean_rho": conf, "model": "cpef"},
    )


def score(
    student: StudentFeatures,
    program: ProgramFeatures,
    *,
    weights: dict[str, float] | None = None,
    cpef_enabled: bool | None = None,
) -> Score:
    """Return a fully-explainable Score for one (student, program) pair.

    When CPEF is enabled (flag or explicit `cpef_enabled=True`) the fused
    Spec-3 score is used; otherwise the legacy convex-sum + hard-filter path.
    """
    if cpef_enabled is None:
        cpef_enabled = _cpef_flag()
    if cpef_enabled:
        return _score_cpef(student, program)

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

    # Only components we can actually evaluate contribute to fitness. cosine
    # needs an embedding on BOTH sides (same dimensionality); absent that, its
    # weight is redistributed across the present components rather than dragging
    # every score down by a dead 0 (see `_renormalized_weights`). soft_align and
    # needs_match always have a defined value via their neutral fallbacks.
    cosine_applied = bool(
        student.embedding and program.embedding and len(student.embedding) == len(program.embedding)
    )
    components: dict[str, float] = {"soft_align": soft_score, "needs_match": needs_score}
    if cosine_applied:
        components["cosine"] = cos_score

    eff_weights = _renormalized_weights(weights, components)
    fitness = sum(eff_weights.get(k, 0.0) * v for k, v in components.items())
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
            # `cosine_applied=False` (no embedding on one side) means the cosine
            # weight was redistributed across the present components — the
            # `weights` below are the effective weights that produced `fitness`.
            "cosine_applied": cosine_applied,
            "weights": eff_weights,
            "nominal_weights": weights,
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
    cpef_enabled: bool | None = None,
) -> list[tuple[ProgramFeatures, Score]]:
    """Score every program and return them sorted by fitness desc.

    `include_eliminated`: if True, eliminated programs are returned at
    the bottom of the list with fitness=0 (useful for the rationale
    agent, which may explain why something was filtered). Under CPEF
    nothing is eliminated — vetoed programs simply sink to the bottom.
    """
    scored = [(p, score(student, p, weights=weights, cpef_enabled=cpef_enabled)) for p in programs]
    if not include_eliminated:
        scored = [(p, s) for p, s in scored if not s.eliminated]
    scored.sort(key=lambda ps: (float(ps[1].fitness), float(ps[1].confidence)), reverse=True)
    return scored
