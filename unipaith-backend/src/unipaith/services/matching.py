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
from .match.params import (
    DEFAULT_PARAMS,
    FIELD_SIM_TABLE,
    clamp01,
    confidence_to_gain,
    prior_for,
    two_sided_confidence,
)

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
# Two-sided confidence (Chart 3 "c = c_student × c_program", Chart 2 "claimed
# program outweighs derived/crawler") is LIVE: each signal's confidence is the
# product of a student-side proxy (StudentFeatures.extractor_quality — the
# upstream per-signal confidence) and a program-side authority proxy
# (ProgramFeatures.data_completeness — claimed ~0.9, derived ~0.5, crawler
# ~0.4). A deeper/cleaner profile and a higher-authority program both move M
# away from the 0.5 prior (sharper); a thin profile or low-authority program
# pull it back toward 0.5.

_CPEF_CONF_FALLBACK = 0.85  # per-side confidence proxy when a feature omits it
_CANONICAL_N = 5  # core fit dimensions for the coverage denominator
#                   (semantic · themes · needs · budget · geo). The optional
#                   per-preference signals (degree_level, field, time,
#                   flexibility, support — each emitted only when the student
#                   states that preference) add to present_a; coverage clamps at
#                   1.0, so a student who expresses many preferences saturates
#                   the damp without ever over-saturating it.


def _student_side_confidence(student: StudentFeatures) -> float:
    """Student-side per-signal confidence proxy (Spec 1) — the upstream
    extractor quality, clamped off the open interval so a fully-confident
    profile still leaves finite precision for the gain."""
    q = student.extractor_quality
    if q is None:
        q = _CPEF_CONF_FALLBACK
    return clamp01(float(q))


def _program_side_confidence(program: ProgramFeatures) -> float:
    """Program-side authority proxy (Spec 2 precedence): a claimed program has
    high data_completeness (~0.9), a derived one lower (~0.5), a crawler one
    lower still (~0.4). This is what makes a claimed program outscore an
    identical-fit derived one."""
    dc = program.data_completeness
    if dc is None:
        dc = _CPEF_CONF_FALLBACK
    return clamp01(float(dc))


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
    w_base = p["w_base"]
    # GAP 1 — real two-sided confidence: c = c_student × c_program. The
    # student-side proxy is the upstream extractor quality (Spec 1); the
    # program-side proxy is the authority-precedence data_completeness (Spec 2,
    # claimed > derived > crawler). rho = confidence_to_gain(c) is the literal
    # weight on the observed fit vs. the 0.5 prior in the posterior-mean.
    c_student = _student_side_confidence(student)
    c_program = _program_side_confidence(program)
    c = two_sided_confidence(c_student, c_program)
    # Each fit signal carries ``c``; ``cpef()`` recomputes its per-signal ``rho``
    # from that. Deal-breakers, by contrast, are HARD ELIGIBILITY facts, not
    # graded fits: the blocking condition is a categorical attribute the program
    # states explicitly (target level, locations, tuition, sponsorship) checked
    # against the student's OWN stated profile. Their certainty is therefore
    # structural — gated by how sure we are of the student's eligibility facts
    # (c_student), NOT damped by the program's free-text data_completeness (a
    # low-authority program can still have an explicit, blocking target level).
    # So a confirmed degree/budget/geo breaker buries even when the program's
    # overall data is sparse — while a THIN student profile (low extractor
    # quality) only dents, matching the "deeper profile → sharper veto" intent.
    veto_rho = confidence_to_gain(c_student, p)
    signals: list[dict[str, Any]] = []

    # semantic (embedding cosine), only when both sides have a matching vector
    if student.embedding and program.embedding and len(student.embedding) == len(program.embedding):
        signals.append(
            {
                "key": "semantic",
                "f": cosine(student.embedding, program.embedding),
                "c": c,
                "w": w_base,
                "prior": prior_for("semantic", p),
            }
        )
    # themes (interest/career/value tag overlap) — always defined via fallbacks
    signals.append(
        {
            "key": "themes",
            "f": soft_align(student, program),
            "c": c,
            "w": w_base,
            "prior": prior_for("themes", p),
        }
    )
    # needs coverage — neutral 0.5 when the student expressed no needs
    signals.append(
        {
            "key": "needs",
            "f": needs_match(student, program),
            "c": c,
            "w": w_base,
            "prior": prior_for("needs", p),
        }
    )

    # field-of-study (GAP — Spec 3 §3 categorical). Graded against the program's
    # offered fields via the curated similarity table: exact → 1.0, related (e.g.
    # data_science↔statistics) → its table value, unrelated → 0.0. Only emitted
    # when the student states a field AND the program lists offered fields, so an
    # absent field injects no phantom dimension. `themes` is interest-tag Jaccard
    # (a soft signal); this is the structural field-vs-fields-offered fit §3 names.
    s_field = s.get("field_of_study")
    p_fields = pr.get("fields_offered") or []
    if s_field is not None and p_fields:
        signals.append(
            {
                "key": "field",
                "f": _fits.fit_categorical_best(s_field, list(p_fields), FIELD_SIM_TABLE),
                "c": c,
                "w": w_base,
                "prior": prior_for("field", p),
            }
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
                "prior": prior_for("budget", p),
            }
        )

    # desired time-to-degree (GAP — Spec 3 §3 numeric-target). Gaussian kernel
    # around the student's desired duration vs the program's length: exact → 1.0,
    # far → 0. Only emitted when the student states a target AND the program lists
    # a duration, so an absent preference injects no phantom dimension.
    s_time = s.get("desired_time_to_degree_months")
    p_duration = pr.get("duration_months")
    if s_time is not None and p_duration is not None:
        signals.append(
            {
                "key": "time",
                "f": _fits.fit_numeric_target(float(p_duration), float(s_time), p["time_h"]),
                "c": c,
                "w": w_base,
                "prior": prior_for("time", p),
            }
        )

    # geo — overlap of preferred vs program locations
    s_geo = s.get("geo_must") or []
    p_locs = pr.get("locations") or []
    if s_geo and p_locs:
        signals.append(
            {
                "key": "geo",
                "f": _fits.fit_geo(s_geo, p_locs),
                "c": c,
                "w": w_base,
                "prior": prior_for("geo", p),
            }
        )

    # flexibility (GAP — Spec 3 §3 boolean). A part-time/online WANT met by the
    # program → 1.0, unmet → 0.0 (hard want floor). Only emitted when the student
    # expresses a flexibility want, so no phantom dimension for students who
    # don't care. A single signal covers both want flavors (the strongest unmet
    # want dominates the floor); the want-strength rides in the weight, not f.
    wants_part_time = bool(s.get("wants_part_time"))
    wants_online = bool(s.get("wants_online"))
    if wants_part_time or wants_online:
        have = False
        if wants_part_time and bool(pr.get("part_time_available")):
            have = True
        if wants_online and bool(pr.get("online_available")):
            have = True
        # If the student wants BOTH and only one is offered, the want is partly
        # unmet → still a hard miss on the floor (have stays True only if every
        # expressed want is satisfied).
        if wants_part_time and not bool(pr.get("part_time_available")):
            have = False
        if wants_online and not bool(pr.get("online_available")):
            have = False
        signals.append(
            {
                "key": "flexibility",
                "f": _fits.fit_boolean(have, want_hard=True),
                "c": c,
                "w": w_base,
                "prior": prior_for("flexibility", p),
            }
        )

    # support (GAP — Spec 3 §3 boolean, soft want). A career-services / support
    # WANT met by the program → 1.0, unmet → 0.3 floor (a soft want, unlike the
    # hard flexibility floor). Only emitted when the student expresses the want.
    if bool(s.get("wants_career_support")):
        signals.append(
            {
                "key": "support",
                "f": _fits.fit_boolean(bool(pr.get("career_services")), want_hard=False),
                "c": c,
                "w": w_base,
                "prior": prior_for("support", p),
            }
        )

    # degree-level fit (GAP 4) — a GRADED signal alongside the veto. Exact level
    # → 1.0, adjacent-acceptable (masters↔doctoral/professional) → 0.6, wrong
    # family → 0.0. Only emitted when the student states an explicit degree-level
    # TARGET (a preference distinct from their current education_level), so we
    # never inject a phantom perfect match for a student with no stated target —
    # the degree *veto* below still handles raw eligibility from education_level.
    # The signal lets an adjacent-acceptable level grade 0.6 instead of reading
    # as a clean 1.0.
    s_lvl = s.get("education_level")
    p_target = pr.get("target_education_level")
    s_degree_target = s.get("degree_level_target")
    if s_degree_target and p_target:
        signals.append(
            {
                "key": "degree_level",
                "f": _fits.fit_degree_level(s_degree_target, p_target),
                "c": c,
                "w": w_base,
                "prior": prior_for("degree_level", p),
            }
        )

    # ── deal-breakers (in-formula veto, not a pre-filter) ──
    dealbreakers: list[dict[str, Any]] = []
    if p_target and s_lvl and s_lvl != "unknown":
        ok = _education_compat(s_lvl, p_target)
        dealbreakers.append({"key": "degree", "v": (1.0 if ok else p["epsilon"]), "rho": veto_rho})
    if s_budget is not None and p_tuition is not None and not s.get("needs_aid", False):
        ceiling = float(s_budget) * (1.0 + p["delta"])
        if float(p_tuition) > ceiling:
            span = max(1e-9, float(s_budget) * p["delta"])
            v = max(p["epsilon"], clamp01(1.0 - (float(p_tuition) - ceiling) / span))
            dealbreakers.append({"key": "budget", "v": v, "rho": veto_rho})
    s_avoid = set(s.get("geo_avoid") or [])
    if s_avoid and p_locs and (s_avoid & set(p_locs)) == set(p_locs):
        dealbreakers.append({"key": "geo_avoid", "v": p["epsilon"], "rho": veto_rho})

    # ── visa FEASIBILITY veto (founder governance, 2026-06-18) ──────────────
    # The founder decided visa/eligibility IS a legitimate consideration — but
    # ONLY in the student's OWN direction (s→p), and ONLY as feasibility, never
    # as selection. The reasoning: a student who needs a study visa literally
    # CANNOT attend a program that cannot enrol / sponsor an international
    # applicant, so that program is INFEASIBLE FOR HER. Sinking it in HER own
    # ranking HELPS her — it steers her away from a guaranteed dead end. This is
    # exactly the asymmetry the fairness rules require:
    #   • s→p (HERE): the student's feasibility may consider her own visa need.
    #   • p→s (cpef_program_to_student): a program ranking APPLICANTS must NEVER
    #     read immigration status — that would make immigration a selection
    #     criterion, which Spec 38 §3/§9 + Spec 46 §6 forbid. That direction
    #     reads only pref_min_gpa / pref_fields / pref_levels and never any visa
    #     key; the fairness contract (tests/test_spec38_fairness_contract.py)
    #     pins both halves of this asymmetry.
    #
    # Confidence-aware + GATED + fail-soft: the veto fires ONLY when the student
    # genuinely needs sponsorship (`needs_visa_sponsorship` projected from her
    # StudentVisaInfo.visa_required) AND the program is KNOWN-cannot-sponsor
    # (`sponsors_international` explicitly False). Unknown sponsorship (key
    # absent) → NO veto (never assume a program can't sponsor). Its trust gain is
    # `veto_rho` (the c_student-gated certainty used by every other deal-breaker),
    # so a thin profile only dents while a confirmed need buries — the same
    # "deeper profile → sharper veto" behaviour as the degree / budget / geo
    # breakers above. A buried-for-the-student program is still display-only to
    # schools; this never changes the program→student direction.
    if s.get("needs_visa_sponsorship") is True and pr.get("sponsors_international") is False:
        dealbreakers.append({"key": "visa_feasibility", "v": p["epsilon"], "rho": veto_rho})

    full_w = _CANONICAL_N * (w_base / 10.0)
    return signals, dealbreakers, full_w


def cpef(
    student: StudentFeatures, program: ProgramFeatures, *, params: dict[str, float] | None = None
) -> tuple[float, dict[str, Any]]:
    """Compute the one CPEF number (student→program direction) + breakdown."""
    p = params or DEFAULT_PARAMS
    signals, dealbreakers, full_w = _build_cpef_signals(student, program, p)

    num = den = present_a = rho_sum = raw_f_sum = 0.0
    sig_bd: list[dict[str, Any]] = []
    for sig in signals:
        rho = confidence_to_gain(sig["c"], p)
        fhat = sig["f"] * rho + (1.0 - rho) * sig["prior"]
        a = (sig["w"] / 10.0) * rho
        num += a * fhat
        den += a
        present_a += a
        rho_sum += rho
        raw_f_sum += sig["f"]
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
        # Tolerant comparison: at the analytic boundary ``v == epsilon`` the float
        # computation of a budget veto can land a hair ABOVE epsilon (e.g.
        # 0.010000000000000009), so a strict ``<=`` would let a confirmed
        # ~1.5x-over-budget program escape the hard floor on float noise. The
        # 1e-9 slack snaps that boundary case to the floor without widening it.
        if db["rho"] >= p["confirmed_gain"] and db["v"] <= p["epsilon"] + 1e-9:
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
        # Spec 3 §4 tie-break ingredients: coverage Σ A_k (present attention) then
        # raw Σ f_k. Exposed so rank_programs can break M-ties by evidence (how
        # much present, confident signal backs the match) rather than by the
        # displayable mean_rho. NOT a sort primary — M is.
        "coverage_sum": round(present_a, 6),
        "raw_fit_sum": round(raw_f_sum, 6),
        "signals": sig_bd,
        "dealbreakers": db_bd,
    }
    return value, breakdown


def cpef_program_to_student(
    student: StudentFeatures, program: ProgramFeatures, *, params: dict[str, float] | None = None
) -> tuple[float, dict[str, Any]]:
    """Reverse direction: how well the student fits the *program's* preferences
    (its target applicant). Returns ``(1.0, {...})`` when the program has no
    preferences yet — an unclaimed program with no derived target applicant has
    no opinion, so it must not pull the blend down."""
    p = params or DEFAULT_PARAMS
    s, pr = student.sparse, program.sparse

    fits_present: list[float] = []
    # academic strength: program's preferred minimum GPA vs the student's GPA
    pref_gpa = pr.get("pref_min_gpa")
    s_gpa = s.get("gpa")
    if pref_gpa is not None and s_gpa is not None:
        fits_present.append(_fits.fit_numeric_higher(float(s_gpa), float(pref_gpa), 0.3))
    # field background: program's preferred fields vs the student's field. Graded
    # via the curated similarity table (Spec 3 §3 categorical), so a related-field
    # applicant (statistics vs a DS program's preferred data_science) reads as a
    # partial fit, not a hard 0 — exact match still scores the full 1.0.
    pref_fields = list(pr.get("pref_fields") or [])
    s_field = s.get("field_of_study")
    if pref_fields and s_field is not None:
        fits_present.append(_fits.fit_categorical_best(s_field, pref_fields, FIELD_SIM_TABLE))
    # applicant level: program's preferred levels vs the student's current level
    pref_levels = set(pr.get("pref_levels") or [])
    s_lvl = s.get("education_level")
    if pref_levels and s_lvl:
        fits_present.append(1.0 if s_lvl in pref_levels else 0.0)

    if not fits_present:
        return 1.0, {"no_prefs": True}

    # A *satisfaction* multiplier, not a fresh fit: perfect match → 1.0 (a
    # well-matched program is never penalized for having preferences), worst
    # match → ``ps_floor`` (pulled down but not buried — burying is the s→p
    # veto's job). No coverage damp / 0.5-shrink here: those belong to the
    # student's own ranking sharpness (s→p), not the program's interest gate.
    sat = sum(fits_present) / len(fits_present)
    floor = p.get("ps_floor", 0.2)

    # GAP 1 (p→s direction) — gate the satisfaction by the program's PREFERENCE
    # confidence (its authority proxy). A program that CLAIMS its preferences
    # (high data_completeness) expresses a confident opinion, so its
    # satisfaction signal moves M more — a poor satisfaction from a claimed
    # preference pulls M down harder; a strong one lifts it more. A DERIVED
    # preference is a softer opinion (lower confidence), so its satisfaction is
    # shrunk toward the neutral 1.0 ("no strong opinion"). rho is the trust gain
    # on the program-side confidence.
    c_program = _program_side_confidence(program)
    rho = confidence_to_gain(c_program, p)
    # Shrink the *gate strength* by rho: at rho→1 a claimed preference applies
    # its full satisfaction multiplier; at rho→0 a barely-trusted preference is
    # nearly inert (value→1.0, "no real opinion"). The neutral anchor is 1.0
    # (the no-prefs value), so a low-confidence preference cannot bury.
    raw = clamp01(floor + (1.0 - floor) * sat)
    value = clamp01(raw * rho + (1.0 - rho) * 1.0)
    return value, {
        "value": round(value, 4),
        "satisfaction": round(sat, 4),
        "raw": round(raw, 4),
        "rho": round(rho, 4),
        "c_program": round(c_program, 4),
        "n_signals": len(fits_present),
        "floor": floor,
    }


def mutual_match(
    student: StudentFeatures, program: ProgramFeatures, *, params: dict[str, float] | None = None
) -> tuple[float, dict[str, Any]]:
    """The rank key ``M`` — a weighted geometric mean of both directions,
    student side leading: ``M = CPEF_{s→p}^alpha * CPEF_{p→s}^(1-alpha)``.
    """
    p = params or DEFAULT_PARAMS
    sp, sp_bd = cpef(student, program, params=p)
    ps, ps_bd = cpef_program_to_student(student, program, params=p)
    a = p["alpha"]
    m = clamp01((sp**a) * (ps ** (1.0 - a)))
    bd = {**sp_bd, "m": round(m, 4), "s2p_value": sp_bd.get("value"), "p2s": ps_bd, "alpha": a}
    return m, bd


def _cpef_flag() -> bool:
    try:
        from unipaith.config import settings

        return bool(getattr(settings, "cpef_matching_enabled", False))
    except Exception:
        return False


def _score_cpef(
    student: StudentFeatures, program: ProgramFeatures, *, params: dict[str, float] | None = None
) -> Score:
    # The persisted fitness IS the rank key M (the two-direction blend). The
    # breakdown keeps the full s→p detail plus the p→s direction and M.
    m, bd = mutual_match(student, program, params=params)
    conf = bd.get("mean_rho", 0.0)
    return Score(
        fitness=Decimal(str(round(m, 4))),
        confidence=Decimal(str(round(conf, 4))),
        eliminated=False,  # nothing is hard-dropped; vetoed programs sink instead
        fitness_breakdown=bd,
        confidence_breakdown={"mean_rho": conf, "model": "cpef", "m": round(m, 4)},
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

    def _sort_key(ps: tuple[ProgramFeatures, Score]) -> tuple[float, float, float]:
        sc = ps[1]
        bd = sc.fitness_breakdown or {}
        if bd.get("model") == "cpef":
            # Spec 3 §4: sort by M desc; ties → coverage Σ A_k, then raw Σ f_k.
            # mean_rho (a displayable certainty the spec says ranking never uses)
            # is deliberately NOT in the key.
            return (
                float(sc.fitness),
                float(bd.get("coverage_sum") or 0.0),
                float(bd.get("raw_fit_sum") or 0.0),
            )
        # Legacy convex-sum path keeps its original (fitness, confidence) key.
        return (float(sc.fitness), float(sc.confidence), 0.0)

    scored.sort(key=_sort_key, reverse=True)
    return scored
