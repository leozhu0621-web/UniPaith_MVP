"""AI Structure — REALISTIC mock-cohort end-to-end exercise (pure Python, no DB).

The sibling ``test_ai_structure_simulation.py`` stress-tests the three charts at
SCALE with a deliberately *random cross-product* cohort — every attribute is
varied independently by index, which makes ~61% of (student, program) pairs trip
the deal-breaker veto (tiny budgets paired with elite tuitions, geo-avoid pinned
on common countries, every-7th student forced incompatible). That is the right
shape for an invariant fuzz test, but it is NOT what a real applicant pool looks
like.

This file builds a CORRELATED, plausible cohort instead and runs it through the
*same* live matcher (``rank_programs(..., cpef_enabled=True)``), then asserts the
three charts visibly hold on realistic data:

  • **Students (~300)** — a real applicant pool. A *selectivity tier* (reach /
    target / safety-leaning) jointly drives GPA **and** standardized test score
    (correlated, not independent). A *field of interest* drives interest themes
    **and** the career arc that actually goes with it (CS→industry, biology→
    clinical/research, …). Budgets are tiered and mostly aid-eligible; geo is a
    home-country preference, rarely a hard avoid. Enrichment depth is tied to a
    *provenance tier* (thin/medium/deep) that sets ``extractor_quality`` +
    ``profile_completeness`` + how many optional signals are populated. Only a
    SMALL, realistic minority carry a genuine deal-breaker (a truly tight no-aid
    budget, a hard geo-avoid, or a wrong degree family).

  • **Schools / programs (~40 schools, ~120 programs)** — each school has a
    selectivity tier that derives its ``pref_min_gpa`` and tuition band; programs
    in a field carry the matching themes/arcs. ProgramPreference provenance is a
    realistic mix: a MINORITY are *claimed* (high ``data_completeness`` ≈ 0.9),
    more are *derived* (≈ 0.5), and the rest have *no opinion* (no prefs → p→s
    neutral 1.0). ``data_completeness`` is itself tiered by provenance.

What it reports + asserts (all on the realistic cohort):
  1. **Veto reach is MUCH lower than the random sim** — well under 20% of pairs
     (the random cross-product was ~61%). Real students aren't randomly broke /
     geo-hostile to most schools.
  2. **M distribution + top-k separation** — top-1 and top-5 means sit clearly
     above the median, so the rank key actually separates good matches from the
     field for a real student.
  3. **The three charts hold on realistic data**:
       - claimed > derived (a claimed program with the same fit lands a sharper M),
       - confidence MOVES M (deeper provenance tier → higher mean M on clean fits),
       - deeper profiles rank SHARPER (higher within-student dispersion).

Run:
  cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true \\
    .venv/bin/pytest tests/test_ai_structure_cohort.py -q

Determinism: a single fixed-seed ``random.Random`` per builder; no wall-clock.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import dataclass
from typing import Any

from unipaith.services.matching import (
    ProgramFeatures,
    StudentFeatures,
    cpef_program_to_student,
    mutual_match,
    rank_programs,
)

_RESULTS_PATH = "/tmp/ai_cohort_results.json"

# ── Realistic, CORRELATED vocabularies ───────────────────────────────────────
# A field of interest determines BOTH the themes a student talks about AND the
# career arc that plausibly follows it — these are not independent draws.

# field → (interest themes, plausible career arcs, typical target degree level)
FIELD_PROFILE: dict[str, dict[str, Any]] = {
    "computer_science": {
        "themes": ["ai", "data_science", "robotics"],
        "arcs": ["industry", "founder", "research"],
        "target": "masters",
    },
    "data_science": {
        "themes": ["data_science", "ai", "finance"],
        "arcs": ["industry", "research", "consulting"],
        "target": "masters",
    },
    "mechanical_engineering": {
        "themes": ["robotics", "sustainability", "design"],
        "arcs": ["industry", "research"],
        "target": "masters",
    },
    "economics": {
        "themes": ["finance", "policy", "data_science"],
        "arcs": ["consulting", "public_sector", "industry"],
        "target": "masters",
    },
    "biology": {
        "themes": ["public_health", "neuroscience", "sustainability"],
        "arcs": ["research", "clinical", "academia"],
        "target": "doctoral",
    },
    "psychology": {
        "themes": ["neuroscience", "public_health", "design"],
        "arcs": ["clinical", "research", "academia"],
        "target": "doctoral",
    },
    "business": {
        "themes": ["finance", "entrepreneurship", "policy"],
        "arcs": ["consulting", "founder", "industry"],
        "target": "professional",
    },
    "public_health": {
        "themes": ["public_health", "policy", "sustainability"],
        "arcs": ["public_sector", "research", "clinical"],
        "target": "masters",
    },
    "environmental_science": {
        "themes": ["sustainability", "policy", "public_health"],
        "arcs": ["research", "public_sector"],
        "target": "masters",
    },
}
FIELDS = list(FIELD_PROFILE.keys())

VALUES = ["impact", "prestige", "community", "innovation", "stability", "diversity"]
NEEDS_TAGS = [
    "financial_aid",
    "mental_health",
    "career_services",
    "housing",
    "disability_support",
    "international_support",
]
SOCIAL_KEYS = ["small_cohort", "urban", "research_intensive", "greek_life", "athletics"]

# Most applicants in this pool are post-bachelor's grad applicants; a minority are
# working professionals returning for a masters. (Both are degree-compatible with
# masters/doctoral/professional, so neither is an artificial deal-breaker.)
EDU_LEVELS = ["bachelors", "bachelors", "bachelors", "working"]  # ~3:1 bachelors:working

# Three selectivity tiers a student self-sorts into. Each ties GPA and test score
# together (a strong applicant tends to be strong on both) — correlated, not
# independent. (gpa_mu on a 4.0 scale; test_mu on a 0–100 percentile-style scale.)
STUDENT_TIERS = [
    {"name": "reach", "gpa_mu": 3.85, "test_mu": 92.0, "weight": 0.30},
    {"name": "target", "gpa_mu": 3.45, "test_mu": 78.0, "weight": 0.45},
    {"name": "safety", "gpa_mu": 3.05, "test_mu": 64.0, "weight": 0.25},
]

# Provenance / enrichment depth tiers. Deeper = more optional signals populated +
# higher extractor_quality + higher profile_completeness. Realistic mix: most
# students have a medium profile; fewer are thin or fully built-out.
DEPTH_TIERS = [
    {"name": "thin", "eq": 0.45, "completeness": 0.40, "weight": 0.25},
    {"name": "medium", "eq": 0.72, "completeness": 0.68, "weight": 0.50},
    {"name": "deep", "eq": 0.93, "completeness": 0.92, "weight": 0.25},
]

# Budget tiers (USD/yr). Most applicants need aid; a tight-no-aid minority is the
# only place a budget deal-breaker can realistically arise.
BUDGET_TIERS = [
    {"name": "constrained", "amount": 25000, "weight": 0.30},
    {"name": "moderate", "amount": 45000, "weight": 0.45},
    {"name": "comfortable", "amount": 75000, "weight": 0.25},
]

# Home countries an applicant prefers (geo_must). A real pool clusters heavily in
# a few markets rather than spreading uniformly.
HOME_COUNTRIES = ["USA", "USA", "USA", "UK", "Canada", "Germany", "Singapore"]


@dataclass
class _Tagged:
    """A built student/program plus the realism labels we score the charts on."""

    sf: Any
    labels: dict[str, Any]


def _weighted_pick(rng, tiers: list[dict[str, Any]]) -> dict[str, Any]:
    r = rng.random()
    acc = 0.0
    for t in tiers:
        acc += t["weight"]
        if r <= acc:
            return t
    return tiers[-1]


def _correlated(rng, mu: float, spread: float, lo: float, hi: float) -> float:
    """A correlated draw around ``mu`` (shared latent ability nudges GPA + tests
    the same direction): one tier-mean + a small common jitter."""
    return round(min(hi, max(lo, mu + rng.uniform(-spread, spread))), 2)


# ── Student cohort ───────────────────────────────────────────────────────────


def make_cohort_students(n: int = 300) -> list[_Tagged]:
    """A correlated, plausible applicant pool of ~300 students."""
    rng = random.Random(20260618)
    out: list[_Tagged] = []
    for i in range(n):
        tier = _weighted_pick(rng, STUDENT_TIERS)
        depth = _weighted_pick(rng, DEPTH_TIERS)
        budget_t = _weighted_pick(rng, BUDGET_TIERS)
        field = rng.choice(FIELDS)
        fp = FIELD_PROFILE[field]
        edu = rng.choice(EDU_LEVELS)

        # A shared latent "strength" nudges GPA and tests TOGETHER (correlated).
        latent = rng.uniform(-1.0, 1.0)
        gpa = round(
            min(4.0, max(2.4, tier["gpa_mu"] + 0.20 * latent + rng.uniform(-0.08, 0.08))), 2
        )
        test = round(
            min(100.0, max(40.0, tier["test_mu"] + 8.0 * latent + rng.uniform(-3.0, 3.0))), 1
        )

        # themes/arcs are drawn FROM the field, scaling with profile depth.
        n_themes = {"thin": 1, "medium": 2, "deep": 3}[depth["name"]]
        themes = fp["themes"][:n_themes]
        n_arcs = {"thin": 1, "medium": 1, "deep": 2}[depth["name"]]
        arcs = fp["arcs"][:n_arcs]
        vals = [rng.choice(VALUES)] if depth["name"] != "thin" else []

        needs_signals: dict[str, float] = {}
        if depth["name"] != "thin":
            tag = rng.choice(NEEDS_TAGS)
            needs_signals[tag] = round(rng.uniform(0.4, 0.95), 2)
            if depth["name"] == "deep":
                tag2 = rng.choice([t for t in NEEDS_TAGS if t != tag])
                needs_signals[tag2] = round(rng.uniform(0.4, 0.95), 2)

        social_prefs: dict[str, float] = {}
        if depth["name"] == "deep":
            social_prefs = {rng.choice(SOCIAL_KEYS): round(rng.uniform(0.5, 0.9), 2)}

        # geo: a home-country preference (geo_must); a hard avoid is rare.
        geo_must = [rng.choice(HOME_COUNTRIES)]
        geo_avoid: list[str] = []

        needs_aid = budget_t["name"] != "comfortable" or rng.random() < 0.4
        budget = budget_t["amount"]

        sparse: dict[str, Any] = {
            "education_level": edu,
            "geo_must": geo_must,
            "geo_avoid": geo_avoid,
            "budget_max_usd_per_year": budget,
            "needs_aid": needs_aid,
            "interest_themes": themes,
            "career_arcs": arcs,
            "values": vals,
            "needs_signals": needs_signals,
            "social_prefs": social_prefs,
            "gpa": gpa,
            "test_score": test,  # carried for realism; matcher reads gpa for p→s
            "field_of_study": field,
            "degree_level_target": fp["target"] if depth["name"] != "thin" else None,
        }

        # ── realistic deal-breaker minority (~8% total, mutually exclusive) ──
        # A genuine, NOT-randomly-assigned blocker: a tight budget with no aid, a
        # hard geo-avoid on the applicant's own market, or a true wrong-family reach.
        dealbreaker = None
        roll = rng.random()
        if roll < 0.03:
            # truly broke + refuses aid (the only honest budget veto)
            sparse["budget_max_usd_per_year"] = 9000
            sparse["needs_aid"] = False
            dealbreaker = "budget"
        elif roll < 0.055:
            # a hard avoid that covers single-location programs in that market
            sparse["geo_avoid"] = ["USA"]
            sparse["geo_must"] = []
            dealbreaker = "geo_avoid"
        elif roll < 0.08:
            # wrong degree family: a high-school-leaver reaching for grad programs
            sparse["education_level"] = "high_school"
            sparse["degree_level_target"] = "bachelors"
            dealbreaker = "degree"

        # A confirmed deal-breaker should come from a profile sure enough of its
        # eligibility FACTS to confirm — give that minority a high extractor_quality.
        eq = 0.95 if dealbreaker else depth["eq"]

        sf = StudentFeatures(
            sparse=sparse,
            embedding=None,  # cold start, mirrors production
            profile_completeness=depth["completeness"],
            extractor_quality=eq,
        )
        out.append(
            _Tagged(
                sf=sf,
                labels={
                    "tier": tier["name"],
                    "depth": depth["name"],
                    "field": field,
                    "dealbreaker": dealbreaker,
                },
            )
        )
    return out


# ── Program catalog ──────────────────────────────────────────────────────────

# School selectivity tiers derive pref_min_gpa + tuition band. Elite schools are
# pickier (higher pref_min_gpa) and pricier; accessible ones are lenient + cheaper.
SCHOOL_TIERS = [
    {"name": "elite", "pref_gpa": 3.8, "tuition": 62000, "weight": 0.25},
    {"name": "strong", "pref_gpa": 3.4, "tuition": 44000, "weight": 0.45},
    {"name": "accessible", "pref_gpa": 3.0, "tuition": 28000, "weight": 0.30},
]

# Program-preference provenance mix (realistic): most programs have NO explicit
# preference yet (unclaimed), a chunk are derived (crawler-inferred), a minority
# are claimed by the institution. data_completeness is tiered by provenance.
PREF_PROVENANCE = [
    {"kind": "none", "dc": 0.45, "weight": 0.45},
    {"kind": "derived", "dc": 0.55, "weight": 0.35},
    {"kind": "claimed", "dc": 0.90, "weight": 0.20},
]

PROG_TARGETS = ["masters", "masters", "doctoral", "professional"]  # masters-heavy


def make_cohort_programs(n_schools: int = 40) -> list[_Tagged]:
    """~40 schools × 2–4 programs (~120 programs), correlated + realistic prefs."""
    rng = random.Random(424242)
    out: list[_Tagged] = []
    for s in range(n_schools):
        tier = _weighted_pick(rng, SCHOOL_TIERS)
        country = rng.choice(HOME_COUNTRIES)
        n_progs = 2 + (s % 3)  # 2..4
        for k in range(n_progs):
            field = rng.choice(FIELDS)
            fp = FIELD_PROFILE[field]
            target = rng.choice(PROG_TARGETS)

            locations = [country]
            if rng.random() < 0.15:  # a few multi-country programs
                locations.append(rng.choice([c for c in HOME_COUNTRIES if c != country]))

            # tuition correlates with selectivity, with mild per-program jitter.
            tuition = int(tier["tuition"] * rng.uniform(0.9, 1.12))

            themes = fp["themes"][: rng.randint(1, 3)]
            arcs = fp["arcs"][:1]
            vals = [rng.choice(VALUES)]

            support: dict[str, float] = {rng.choice(NEEDS_TAGS): round(rng.uniform(0.5, 0.9), 2)}
            if rng.random() < 0.4:
                support[rng.choice(NEEDS_TAGS)] = round(rng.uniform(0.5, 0.9), 2)

            sparse: dict[str, Any] = {
                "target_education_level": target,
                "locations": locations,
                "tuition_usd_per_year": tuition,
                "interest_themes": themes,
                "career_arcs": arcs,
                "values": vals,
                "support_signals": support,
                "social_features": {rng.choice(SOCIAL_KEYS): round(rng.uniform(0.5, 0.8), 2)},
            }

            prov = _weighted_pick(rng, PREF_PROVENANCE)
            if prov["kind"] != "none":
                # a real preference, derived from the school's selectivity tier
                sparse["pref_min_gpa"] = round(tier["pref_gpa"] + rng.uniform(-0.1, 0.1), 2)
                sparse["pref_fields"] = [field, fp["arcs"][0]]  # field + a related tag
                sparse["pref_levels"] = ["bachelors", "working"]

            # a realistic minority carry a display-only ranking — must be IGNORED.
            if rng.random() < 0.2:
                sparse["ranking"] = rng.randint(1, 100)
                sparse["weight_ranking"] = round(rng.uniform(0.1, 0.9), 2)

            pf = ProgramFeatures(
                program_id=f"school_{s:02d}_p{k}",
                sparse=sparse,
                embedding=None,
                data_completeness=prov["dc"],
            )
            out.append(
                _Tagged(
                    sf=pf,
                    labels={
                        "school_tier": tier["name"],
                        "field": field,
                        "pref_kind": prov["kind"],
                    },
                )
            )
    return out


# ── Build once (module-level, deterministic) ─────────────────────────────────

_STUDENTS = make_cohort_students(300)
_PROGRAMS = make_cohort_programs(40)
_PROG_SF = [t.sf for t in _PROGRAMS]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    k = (len(xs) - 1) * (pct / 100.0)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return xs[int(k)]
    return xs[lo] * (hi - k) + xs[hi] * (k - lo)


def run_cohort() -> dict[str, Any]:
    """Rank every realistic student against the catalog; collect aggregate stats."""
    all_m: list[float] = []
    top1: list[float] = []
    top5_mean: list[float] = []
    median_per_student: list[float] = []
    within_dispersion: list[float] = []
    n_pairs = 0
    n_vetoed = 0
    n_hard_floor = 0
    n_no_opinion = 0
    exceptions = 0

    # per provenance-tier mean M on CLEAN (un-vetoed) pairs → "confidence moves M".
    depth_clean_m: dict[str, list[float]] = {"thin": [], "medium": [], "deep": []}
    # within-student dispersion by depth → "deeper profiles rank sharper".
    depth_dispersion: dict[str, list[float]] = {"thin": [], "medium": [], "deep": []}

    db_total = 0
    db_buried_ok = 0

    for st in _STUDENTS:
        try:
            ranked = rank_programs(st.sf, _PROG_SF, cpef_enabled=True, include_eliminated=True)
        except Exception:  # pragma: no cover - any raise is a hard downstream fail
            exceptions += 1
            continue
        ms = [float(sc.fitness) for _, sc in ranked]
        all_m.extend(ms)
        n_pairs += len(ms)
        if ms:
            top1.append(ms[0])
            top5_mean.append(statistics.mean(ms[: min(5, len(ms))]))
            median_per_student.append(statistics.median(ms))
            if len(ms) > 1:
                disp = statistics.pstdev(ms)
                within_dispersion.append(disp)
                depth_dispersion[st.labels["depth"]].append(disp)

        for _, sc in ranked:
            bd = sc.fitness_breakdown
            if bd.get("veto", 1.0) < 0.999:
                n_vetoed += 1
            if bd.get("hard_floor"):
                n_hard_floor += 1
            if bd.get("p2s", {}).get("no_prefs"):
                n_no_opinion += 1
            # clean, un-vetoed pair → record its M against the student's depth
            if not bd.get("hard_floor") and bd.get("veto", 1.0) >= 0.999:
                depth_clean_m[st.labels["depth"]].append(float(sc.fitness))

        if st.labels["dealbreaker"]:
            db_total += 1
            clean_min = min(
                (
                    float(sc.fitness)
                    for _, sc in ranked
                    if not sc.fitness_breakdown.get("hard_floor")
                ),
                default=None,
            )
            hard_max = max(
                (float(sc.fitness) for _, sc in ranked if sc.fitness_breakdown.get("hard_floor")),
                default=None,
            )
            if hard_max is None or clean_min is None or hard_max < clean_min:
                db_buried_ok += 1

    stats: dict[str, Any] = {
        "n_students": len(_STUDENTS),
        "n_programs": len(_PROG_SF),
        "n_pairs": n_pairs,
        "exceptions": exceptions,
        "m_min": round(min(all_m), 4) if all_m else None,
        "m_max": round(max(all_m), 4) if all_m else None,
        "m_mean": round(statistics.mean(all_m), 4) if all_m else None,
        "m_median": round(statistics.median(all_m), 4) if all_m else None,
        "m_stdev": round(statistics.pstdev(all_m), 4) if len(all_m) > 1 else None,
        "m_p10": round(_percentile(all_m, 10), 4) if all_m else None,
        "m_p90": round(_percentile(all_m, 90), 4) if all_m else None,
        "top1_mean": round(statistics.mean(top1), 4) if top1 else None,
        "top5_mean": round(statistics.mean(top5_mean), 4) if top5_mean else None,
        "median_per_student_mean": (
            round(statistics.mean(median_per_student), 4) if median_per_student else None
        ),
        "within_student_dispersion_mean": (
            round(statistics.mean(within_dispersion), 4) if within_dispersion else None
        ),
        "pct_pairs_vetoed": round(100 * n_vetoed / n_pairs, 2) if n_pairs else None,
        "pct_pairs_hard_floor": round(100 * n_hard_floor / n_pairs, 2) if n_pairs else None,
        "pct_pairs_no_opinion": round(100 * n_no_opinion / n_pairs, 2) if n_pairs else None,
        "depth_clean_m_mean": {
            d: (round(statistics.mean(v), 4) if v else None) for d, v in depth_clean_m.items()
        },
        "depth_dispersion_mean": {
            d: (round(statistics.mean(v), 4) if v else None) for d, v in depth_dispersion.items()
        },
        "dealbreaker_students": db_total,
        "dealbreaker_buried_ok": db_buried_ok,
        "distinct_m_values": len({round(m, 4) for m in all_m}),
    }
    with open(_RESULTS_PATH, "w") as fh:
        json.dump(stats, fh, indent=2)
    return stats


_STATS = run_cohort()


def print_stats() -> dict[str, Any]:
    """Run the cohort and print the aggregate stats (callable from a REPL)."""
    print(json.dumps(_STATS, indent=2))
    return _STATS


# ── Realism + shape tests ────────────────────────────────────────────────────


def test_cohort_shape_and_no_exceptions():
    """~300 correlated students × ~120 programs, every pair scored, zero raises."""
    assert _STATS["n_students"] == 300
    assert 90 <= _STATS["n_programs"] <= 160
    assert _STATS["exceptions"] == 0
    assert _STATS["n_pairs"] == _STATS["n_students"] * _STATS["n_programs"]
    # bounded + non-degenerate
    assert 0.0 <= _STATS["m_min"] <= _STATS["m_max"] <= 1.0
    assert _STATS["m_stdev"] > 0.02
    assert _STATS["distinct_m_values"] > 50


def test_realistic_cohort_is_correlated_not_random_cross_product():
    """REALISM — the cohort is correlated, not the prior independent cross-product:
    a student's GPA tracks their selectivity tier, and their themes/arcs come from
    their field (so a CS applicant talks about ai/data_science, not random tags)."""
    by_tier: dict[str, list[float]] = {"reach": [], "target": [], "safety": []}
    for st in _STUDENTS:
        by_tier[st.labels["tier"]].append(st.sf.sparse["gpa"])
    # GPA is monotone in selectivity tier — proof the attributes are correlated.
    assert statistics.mean(by_tier["reach"]) > statistics.mean(by_tier["target"])
    assert statistics.mean(by_tier["target"]) > statistics.mean(by_tier["safety"])
    # themes are drawn from the field, never empty, and a subset of the field's set
    for st in _STUDENTS:
        fp = FIELD_PROFILE[st.labels["field"]]
        assert st.sf.sparse["interest_themes"], "every student carries a field-driven theme"
        assert set(st.sf.sparse["interest_themes"]) <= set(fp["themes"])


def test_veto_reach_far_below_random_cross_product():
    """CHART 3 / REALISM — on a realistic pool the deal-breaker veto reaches a SMALL
    fraction of pairs: WELL under 20% (the random cross-product sim reaches ~61%).
    Real applicants are not randomly broke / geo-hostile to most schools."""
    assert _STATS["pct_pairs_vetoed"] is not None
    assert _STATS["pct_pairs_vetoed"] < 20.0, _STATS["pct_pairs_vetoed"]
    # hard-floored pairs (CONFIRMED deal-breakers) are rarer still — only the ~8%
    # deal-breaker minority, against the programs they truly block on.
    assert _STATS["pct_pairs_hard_floor"] < 10.0, _STATS["pct_pairs_hard_floor"]
    # and the deal-breaker students that DO carry one get it buried below clean.
    assert _STATS["dealbreaker_students"] > 0
    assert _STATS["dealbreaker_buried_ok"] == _STATS["dealbreaker_students"]


def test_topk_separation_rank_key_actually_sorts_the_field():
    """CHART 3 — the rank key M SEPARATES: the mean top-1 and top-5 scores sit
    clearly above the population median, so a real student's best matches stand out
    from the field (not a flat list)."""
    assert _STATS["top1_mean"] > _STATS["m_median"] + 0.05, _STATS
    assert _STATS["top5_mean"] > _STATS["m_median"] + 0.02, _STATS
    assert _STATS["top1_mean"] >= _STATS["top5_mean"], _STATS
    # the p90/p10 spread is meaningful → the distribution isn't a spike
    assert _STATS["m_p90"] - _STATS["m_p10"] > 0.05, _STATS


def test_no_opinion_programs_are_present_but_not_a_majority():
    """CHART 2 — unclaimed (no-preference) programs exist and stay NEUTRAL (p→s 1.0),
    but they do NOT dominate: a realistic catalog has a real chunk of derived/claimed
    preferences too, so 'no opinion' is a minority of the (student,program) pairs."""
    # ~45% of programs are no-pref → no-opinion pairs land near that, never ~100%.
    assert _STATS["pct_pairs_no_opinion"] is not None
    assert 25.0 < _STATS["pct_pairs_no_opinion"] < 65.0, _STATS["pct_pairs_no_opinion"]
    # and a no-pref program genuinely scores neutral p→s for a real student
    no_pref = [t.sf for t in _PROGRAMS if t.labels["pref_kind"] == "none"]
    assert no_pref, "cohort must contain no-preference programs"
    ps, bd = cpef_program_to_student(_STUDENTS[0].sf, no_pref[0])
    assert ps == 1.0 and bd.get("no_prefs") is True


# ── Chart 2: claimed > derived surfaces on realistic data ────────────────────


def test_claimed_outscores_derived_on_a_realistic_well_fit_pair():
    """CHART 2 ('claimed > derived surfaces') — pick a real student and a real
    program they fit well, then compare the SAME program at claimed vs derived vs
    none authority. On an above-prior fit, higher authority lands a sharper M."""
    student = _STUDENTS[0].sf
    fp = FIELD_PROFILE[_STUDENTS[0].labels["field"]]
    base = {
        "target_education_level": fp["target"],
        "locations": student.sparse.get("geo_must") or ["USA"],
        "tuition_usd_per_year": 30000,
        "interest_themes": fp["themes"],
        "career_arcs": fp["arcs"][:1],
        "values": student.sparse.get("values") or ["impact"],
    }
    by_kind: dict[str, float] = {}
    for kind, dc in (("claimed", 0.9), ("derived", 0.5), ("none", 0.4)):
        prog = ProgramFeatures(program_id=f"p_{kind}", sparse=dict(base), data_completeness=dc)
        m, _ = mutual_match(student, prog)
        by_kind[kind] = m
    # all distinct, and ordered by authority on a strong (above-prior) fit
    assert len({round(v, 10) for v in by_kind.values()}) == 3, by_kind
    assert by_kind["claimed"] > by_kind["derived"] > by_kind["none"], by_kind


def test_confidence_moves_m_deeper_provenance_higher_clean_mean():
    """CHART 2/3 ('confidence moves M') — across the realistic cohort, the mean M on
    CLEAN (un-vetoed) pairs rises monotonically with the student's provenance depth:
    thin < medium < deep. A deeper, higher-confidence profile sharpens an above-prior
    fit upward, so its clean matches score higher on average."""
    means = _STATS["depth_clean_m_mean"]
    assert means["thin"] is not None and means["medium"] is not None and means["deep"] is not None
    assert means["thin"] < means["medium"] < means["deep"], means


def test_deeper_profiles_rank_sharper_within_student_dispersion():
    """CHART 3 ('deeper profiles rank sharper') — a deeper profile produces a more
    DISPERSED within-student ranking (the coverage damp lets more signals separate
    the field), so mean within-student dispersion rises with provenance depth."""
    disp = _STATS["depth_dispersion_mean"]
    assert disp["thin"] is not None and disp["deep"] is not None
    # deep is strictly sharper than thin; medium sits between (allow the mild
    # overlap that real correlated data can produce between adjacent tiers).
    assert disp["deep"] > disp["thin"], disp
    assert disp["deep"] >= disp["medium"] >= disp["thin"] - 1e-9, disp


def test_ranking_key_excluded_on_realistic_programs():
    """CHART 2 — a program's display-only 'ranking'/'weight_ranking' never enters M.
    Stripping it leaves M byte-identical on a realistic (student, program) pair."""
    with_ranking = [t.sf for t in _PROGRAMS if "ranking" in t.sf.sparse]
    assert with_ranking, "cohort must contain programs carrying a display ranking"
    stu = _STUDENTS[7].sf
    for prog in with_ranking[:20]:
        stripped = ProgramFeatures(
            program_id=prog.program_id,
            sparse={k: v for k, v in prog.sparse.items() if k not in ("ranking", "weight_ranking")},
            embedding=prog.embedding,
            data_completeness=prog.data_completeness,
        )
        m_full = float(rank_programs(stu, [prog], cpef_enabled=True)[0][1].fitness)
        m_strip = float(rank_programs(stu, [stripped], cpef_enabled=True)[0][1].fitness)
        assert m_full == m_strip, f"ranking key leaked into M for {prog.program_id}"


def test_every_m_bounded_and_finite_on_cohort():
    """CHART 3 invariant on realistic data — every M and confidence ∈ [0,1], finite."""
    for st in _STUDENTS[::5]:
        ranked = rank_programs(st.sf, _PROG_SF, cpef_enabled=True, include_eliminated=True)
        for prog, sc in ranked:
            m = float(sc.fitness)
            assert 0.0 <= m <= 1.0 and not math.isnan(m) and not math.isinf(m), prog.program_id
            c = float(sc.confidence)
            assert 0.0 <= c <= 1.0 and not math.isnan(c)


def test_strong_applicant_satisfies_picky_program_better_than_weak_one():
    """CHART 2 (p→s direction, realistic) — a high-GPA reach applicant satisfies an
    elite program's claimed preference (pref_min_gpa) MORE than a low-GPA safety
    applicant does, so the same picky program pulls the strong student's M down less."""
    elite = ProgramFeatures(
        program_id="elite_claimed",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 60000,
            "interest_themes": ["ai", "data_science"],
            "career_arcs": ["industry"],
            "pref_min_gpa": 3.8,
            "pref_fields": ["computer_science", "industry"],
            "pref_levels": ["bachelors", "working"],
        },
        data_completeness=0.9,  # claimed
    )
    strong = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "interest_themes": ["ai", "data_science"],
            "career_arcs": ["industry"],
            "gpa": 3.9,
            "field_of_study": "computer_science",
        },
        extractor_quality=0.9,
    )
    weak = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "interest_themes": ["ai", "data_science"],
            "career_arcs": ["industry"],
            "gpa": 2.9,
            "field_of_study": "computer_science",
        },
        extractor_quality=0.9,
    )
    ps_strong, _ = cpef_program_to_student(strong, elite)
    ps_weak, _ = cpef_program_to_student(weak, elite)
    assert ps_strong > ps_weak, (ps_strong, ps_weak)
    m_strong, _ = mutual_match(strong, elite)
    m_weak, _ = mutual_match(weak, elite)
    assert m_strong > m_weak, (m_strong, m_weak)
