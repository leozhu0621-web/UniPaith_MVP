"""AI Structure — scale-validation simulation + invariant test (pure Python, no DB).

Stress-tests the three charts of the live AI Structure at scale:

  Chart 1 (ENRICH) — `enrichment_planner`: essentials → high-value → standard;
    ask before confirm; skip confirmed; essentials_present gates matching;
    school ranking is NEVER asked.
  Chart 2 (SCHOOL/PROGRAM) — a program with no ProgramPreference has "no opinion"
    (p→s neutral 1.0); a claimed (high data_completeness) preference outweighs a
    derived (lower) one only via two-sided confidence — note where that does/doesn't
    bite today. A 'ranking'/'weight_ranking' key on a program is EXCLUDED from the math.
  Chart 3 (MATCH) — ONE backend number M = CPEF_{s→p}^alpha · CPEF_{p→s}^(1-alpha),
    alpha≈0.7; M is the rank key; deal-breakers are an in-formula VETO with a hardened
    floor; coverage damp; everything bounded [0,1]; no NaN; no phantom-zero.

    HONEST COVERAGE NOTES (Slice A):
      • A CONFIRMED deal-breaker is capped at ``epsilon·inner`` and ranks below every
        clean program of comparable-or-better inner fit (and below every truly
        un-vetoed program); it is NOT guaranteed below every *soft*-vetoed program —
        see test_honest_note_confirmed_dealbreaker_not_below_every_clean.
      • The 'an INFERRED deal-breaker only dents' branch is UNREACHABLE today: every
        veto rho is the uniform Slice-A constant, so all deal-breakers are confirmed.
        The graded-dent math is correct but cannot vary at runtime until real
        per-signal confidence is wired (pinned by the Slice-A confidence tests below).

This builds 1000 diverse students × ~50 schools / ~230 programs, ranks every student
against every program under CPEF, dumps aggregate stats + a JSON to
/tmp/ai_sim_results.json, and asserts the invariants we can encode today.

Run:
  cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true \\
    .venv/bin/pytest tests/test_ai_structure_simulation.py -q

Determinism: everything is seeded by index (a single fixed-seed random.Random
for the few jitter knobs). No wall-clock, no unseeded randomness.
"""

from __future__ import annotations

import json
import math
import random
import statistics
from typing import Any

from unipaith.services.enrichment_planner import (
    CATALOG,
    ESSENTIAL_KEYS,
    action_for,
    essentials_present,
    plan_next,
)
from unipaith.services.match import fits as _fits
from unipaith.services.match.params import DEFAULT_PARAMS, confidence_to_gain
from unipaith.services.matching import (
    ProgramFeatures,
    StudentFeatures,
    cpef,
    cpef_program_to_student,
    mutual_match,
    rank_programs,
)

# ── Small, fixed vocabularies (varied by index, deterministic) ───────────────

_RESULTS_PATH = "/tmp/ai_sim_results.json"

EDU_LEVELS = ["high_school", "bachelors", "masters", "working", "gap_year"]
COUNTRIES = ["USA", "UK", "Canada", "Germany", "Australia", "Singapore", "Netherlands"]
FIELDS = [
    "computer_science",
    "data_science",
    "mechanical_engineering",
    "economics",
    "biology",
    "psychology",
    "business",
    "law",
    "medicine",
    "art_history",
    "physics",
    "education",
    "nursing",
    "political_science",
    "environmental_science",
]
INTEREST_THEMES = [
    "data_science",
    "ai",
    "sustainability",
    "finance",
    "robotics",
    "public_health",
    "design",
    "policy",
    "neuroscience",
    "entrepreneurship",
]
CAREER_ARCS = [
    "research",
    "industry",
    "founder",
    "public_sector",
    "clinical",
    "academia",
    "consulting",
]
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

# ── Builders ─────────────────────────────────────────────────────────────────


def make_students(n: int = 1000) -> list[StudentFeatures]:
    """1000 diverse students, fully deterministic by index.

    Varies education level, geo must/avoid, budget, aid flag, interest/career/value
    tags, needs map, gpa, field, profile_completeness, and (crucially) ENRICHMENT
    DEPTH + per-signal confidence — modeled via a confidence knob derived from index.

    A deal-breaker subset carries a hard-veto condition:
      - i % 21 == 0  → reaches for a degree-INCOMPATIBLE level (wrong family)
      - i % 21 == 7  → way-over budget on most programs (tiny budget, no aid)
      - i % 21 == 14 → geo_avoid covers a country many programs sit in

    (No immigration/eligibility deal-breaker is modeled — see the GAP-3 deferral
    note in matching.py: the fairness contract Spec 38 §3/§9 + Spec 46 §6 keeps
    immigration status out of ranking, so the matcher never vetoes on it.)
    """
    rng = random.Random(20260618)
    students: list[StudentFeatures] = []
    for i in range(n):
        edu = EDU_LEVELS[i % len(EDU_LEVELS)]

        # Enrichment depth: a third are "essentials-only / thin", a third "medium",
        # a third "full / deep". Drives profile_completeness AND how many optional
        # signals are populated.
        depth = i % 3  # 0 thin, 1 medium, 2 deep
        completeness = {0: 0.35, 1: 0.65, 2: 0.92}[depth]

        # geo: half the students pin a must-country; a sixth name an avoid-country.
        geo_must = [COUNTRIES[i % len(COUNTRIES)]] if i % 2 == 0 else []
        geo_avoid = [COUNTRIES[(i + 3) % len(COUNTRIES)]] if i % 6 == 0 else []

        budget = 15000 + (i * 137 % 65001)  # 15k–80k, spread deterministically
        needs_aid = (i % 4) == 0

        themes = [INTEREST_THEMES[i % len(INTEREST_THEMES)]]
        if depth >= 1:
            themes.append(INTEREST_THEMES[(i + 4) % len(INTEREST_THEMES)])
        arcs = [CAREER_ARCS[i % len(CAREER_ARCS)]]
        if depth == 2:
            arcs.append(CAREER_ARCS[(i + 2) % len(CAREER_ARCS)])
        vals = [VALUES[i % len(VALUES)]] if depth >= 1 else []

        # needs map only on medium/deep profiles; severities in [0.3, 1.0]
        needs_signals: dict[str, float] = {}
        if depth >= 1:
            tag = NEEDS_TAGS[i % len(NEEDS_TAGS)]
            needs_signals[tag] = round(0.3 + (i % 8) / 10.0, 2)
            if depth == 2:
                tag2 = NEEDS_TAGS[(i + 2) % len(NEEDS_TAGS)]
                needs_signals[tag2] = round(0.3 + ((i + 3) % 8) / 10.0, 2)

        social_prefs: dict[str, float] = {}
        if depth == 2:
            social_prefs = {
                SOCIAL_KEYS[i % len(SOCIAL_KEYS)]: round(0.4 + (i % 6) / 10.0, 2),
            }

        gpa = round(2.0 + (i * 0.0021 % 2.0), 2)  # 2.0–4.0
        field = FIELDS[i % len(FIELDS)]

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
            "field_of_study": field,
        }

        # ── deal-breaker subset (every 7th student) ──
        if i % 21 == 0:
            # wrong degree family: a bachelors-holder reaching for a *bachelors*
            # program (handled below by tagging them so make_schools can't be the
            # cause); we encode it by giving high_school students a masters reach is
            # invalid — simplest: set education_level so the matcher's compat table
            # rejects the common masters programs.  A "working" student aiming at a
            # bachelors program is incompatible (working → masters/doctoral/prof only).
            sparse["education_level"] = "working"
            sparse["_dealbreaker"] = "degree"  # marker for the test (ignored by matcher)
        elif i % 21 == 7:
            sparse["budget_max_usd_per_year"] = 8000  # below nearly every tuition
            sparse["needs_aid"] = False  # aid would waive the veto
            sparse["_dealbreaker"] = "budget"
        elif i % 21 == 14:
            # geo_avoid that will cover single-location programs in that country
            sparse["geo_avoid"] = ["USA"]
            sparse["geo_must"] = []
            sparse["_dealbreaker"] = "geo_avoid"

        # jitter completeness a hair so confidence isn't perfectly tiered (still seeded)
        completeness = round(min(1.0, max(0.0, completeness + rng.uniform(-0.05, 0.05))), 3)

        # A confirmed deal-breaker must come from a HIGH-confidence profile (so the
        # structural veto_rho clears confirmed_gain). Give the deal-breaker subset a
        # high extractor_quality so the veto confirms regardless of enrichment depth.
        eq = 0.95 if sparse.get("_dealbreaker") else round(0.6 + depth * 0.15, 3)

        students.append(
            StudentFeatures(
                sparse=sparse,
                embedding=None,  # cold-start: no embeddings (mirrors production today)
                profile_completeness=completeness,
                extractor_quality=eq,
            )
        )
    return students


def make_schools(n: int = 50) -> tuple[list[dict[str, Any]], list[ProgramFeatures]]:
    """50 schools, each owning 3–6 programs (~230 programs total).

    Programs vary target level, locations, tuition (10k–90k), tag sets, support
    signals, and a ProgramPreference on MOST (pref_min_gpa / pref_fields /
    pref_levels). Preference provenance is mixed:
      - "claimed"  → high data_completeness (0.9)
      - "derived"  → lower data_completeness (0.5)
      - none       → no prefs at all (no opinion → p→s neutral 1.0)
    A few programs carry a 'ranking' / 'weight_ranking' key to prove it's EXCLUDED.

    Returns (schools_meta, all_programs).
    """
    rng = random.Random(424242)
    schools: list[dict[str, Any]] = []
    programs: list[ProgramFeatures] = []
    target_levels = ["bachelors", "masters", "doctoral", "professional"]

    for s in range(n):
        n_progs = 3 + (s % 4)  # 3..6
        country = COUNTRIES[s % len(COUNTRIES)]
        school_id = f"school_{s:02d}"
        prog_ids: list[str] = []
        for k in range(n_progs):
            gi = s * 10 + k  # global program index for deterministic variation
            pid = f"{school_id}_p{k}"
            prog_ids.append(pid)

            target = target_levels[gi % len(target_levels)]
            # most programs single-location (the school's country); some multi-country
            locations = [country]
            if gi % 5 == 0:
                locations.append(COUNTRIES[(s + 2) % len(COUNTRIES)])

            tuition = 10000 + (gi * 211 % 80001)  # 10k–90k
            themes = [INTEREST_THEMES[gi % len(INTEREST_THEMES)]]
            if gi % 3 == 0:
                themes.append(INTEREST_THEMES[(gi + 5) % len(INTEREST_THEMES)])
            arcs = [CAREER_ARCS[gi % len(CAREER_ARCS)]]
            vals = [VALUES[gi % len(VALUES)]]

            support: dict[str, float] = {
                NEEDS_TAGS[gi % len(NEEDS_TAGS)]: round(0.5 + (gi % 5) / 10.0, 2),
            }
            if gi % 4 == 0:
                support[NEEDS_TAGS[(gi + 1) % len(NEEDS_TAGS)]] = 0.8

            sparse: dict[str, Any] = {
                "target_education_level": target,
                "locations": locations,
                "tuition_usd_per_year": tuition,
                "interest_themes": themes,
                "career_arcs": arcs,
                "values": vals,
                "support_signals": support,
                "social_features": {SOCIAL_KEYS[gi % len(SOCIAL_KEYS)]: 0.7},
            }

            # ── ProgramPreference provenance (Chart 2) ──
            # gi % 4 == 3 → NO prefs (no opinion); 0/1 → claimed; 2 → derived.
            pref_mode = gi % 4
            if pref_mode == 3:
                data_completeness = 0.5
                pref_kind = "none"
            else:
                # add a preference; the *strictness* varies so some students fail it
                sparse["pref_min_gpa"] = round(2.8 + (gi % 6) * 0.18, 2)  # 2.8–3.7
                sparse["pref_fields"] = [
                    FIELDS[gi % len(FIELDS)],
                    FIELDS[(gi + 1) % len(FIELDS)],
                ]
                sparse["pref_levels"] = [EDU_LEVELS[gi % len(EDU_LEVELS)]]
                if pref_mode == 2:
                    data_completeness = 0.5  # derived
                    pref_kind = "derived"
                else:
                    data_completeness = 0.9  # claimed
                    pref_kind = "claimed"

            # A few programs carry a ranking key — must be IGNORED by the math.
            if gi % 11 == 0:
                sparse["ranking"] = 1 + (gi % 100)
                sparse["weight_ranking"] = round(rng.uniform(0.1, 0.9), 2)

            programs.append(
                ProgramFeatures(
                    program_id=pid,
                    sparse=sparse,
                    embedding=None,
                    data_completeness=data_completeness,
                )
            )
            # stash pref kind on the dataclass for the stats pass (not read by matcher)
            programs[-1]._pref_kind = pref_kind  # type: ignore[attr-defined]

        schools.append({"id": school_id, "country": country, "program_ids": prog_ids})
    return schools, programs


# ── Signal-state builder for the enrichment-planner sweep (Chart 1) ──────────


def make_signal_states(n: int = 1000) -> list[dict[str, dict[str, Any]]]:
    """1000 varied enrichment signal-states for the planner.

    Each field is independently missing / inferred (weak) / imported (okay) /
    confirmed (solid), seeded by index so the mix is reproducible but diverse.
    """
    rng = random.Random(7)
    states: list[dict[str, dict[str, Any]]] = []
    for i in range(n):
        state: dict[str, dict[str, Any]] = {}
        for j, field in enumerate(CATALOG):
            key = field["key"]
            roll = (i * 31 + j * 17 + rng.randint(0, 3)) % 4
            if roll == 0:
                continue  # missing → absent from state (planner treats as ask)
            if roll == 1:
                conf = round(0.2 + (i % 3) * 0.1, 2)  # inferred/weak → ask
            elif roll == 2:
                conf = round(0.55 + (i % 3) * 0.1, 2)  # imported/okay → confirm
            else:
                conf = round(0.9, 2)  # confirmed → skip
            state[key] = {"value": f"v_{key}_{i}", "confidence": conf, "source": "sim"}
        states.append(state)
    return states


# ── The match run ────────────────────────────────────────────────────────────


def run_matches(
    students: list[StudentFeatures] | None = None,
    programs: list[ProgramFeatures] | None = None,
    *,
    dump: bool = True,
) -> dict[str, Any]:
    """Rank every student against all programs under CPEF; collect aggregate stats.

    Returns a stats dict and (optionally) dumps it to /tmp/ai_sim_results.json.
    """
    students = students if students is not None else make_students(1000)
    if programs is None:
        _, programs = make_schools(50)

    all_m: list[float] = []
    top1_m: list[float] = []
    top10_mean: list[float] = []
    n_vetoed_pairs = 0
    n_hard_floor_pairs = 0
    n_no_opinion_pairs = 0
    n_pairs = 0
    coverage_vals: list[float] = []
    per_student_dispersion: list[float] = []
    exceptions = 0

    # deal-breaker bookkeeping: for the marked students, did their worst
    # (intended-veto) program land below every clean program?
    db_buried_ok = 0
    db_total = 0

    for stu in students:
        try:
            ranked = rank_programs(stu, programs, cpef_enabled=True, include_eliminated=True)
        except Exception:  # pragma: no cover - any raise is a hard fail downstream
            exceptions += 1
            continue
        ms = [float(sc.fitness) for _, sc in ranked]
        all_m.extend(ms)
        n_pairs += len(ms)
        if ms:
            top1_m.append(ms[0])
            top10_mean.append(statistics.mean(ms[: min(10, len(ms))]))
            if len(ms) > 1:
                per_student_dispersion.append(statistics.pstdev(ms))
        for _, sc in ranked:
            bd = sc.fitness_breakdown
            if bd.get("veto", 1.0) < 0.999:
                n_vetoed_pairs += 1
            if bd.get("hard_floor"):
                n_hard_floor_pairs += 1
            if "coverage" in bd:
                coverage_vals.append(bd["coverage"])
            if bd.get("p2s", {}).get("no_prefs"):
                n_no_opinion_pairs += 1

        # deal-breaker subset: confirm a hard-floored program ranks below all clean
        if stu.sparse.get("_dealbreaker"):
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
            if hard_max is None:
                # no hard-floored program for this student (e.g. geo_avoid never
                # fully covered a program's locations) — not a failure, just N/A
                db_buried_ok += 1
            elif clean_min is None or hard_max < clean_min:
                db_buried_ok += 1

    stats: dict[str, Any] = {
        "n_students": len(students),
        "n_programs": len(programs),
        "n_pairs": n_pairs,
        "exceptions": exceptions,
        "m_min": round(min(all_m), 4) if all_m else None,
        "m_max": round(max(all_m), 4) if all_m else None,
        "m_mean": round(statistics.mean(all_m), 4) if all_m else None,
        "m_median": round(statistics.median(all_m), 4) if all_m else None,
        "m_stdev": round(statistics.pstdev(all_m), 4) if len(all_m) > 1 else None,
        "m_p10": round(_pct(all_m, 10), 4) if all_m else None,
        "m_p90": round(_pct(all_m, 90), 4) if all_m else None,
        "top1_mean": round(statistics.mean(top1_m), 4) if top1_m else None,
        "top10_mean": round(statistics.mean(top10_mean), 4) if top10_mean else None,
        "per_student_dispersion_mean": (
            round(statistics.mean(per_student_dispersion), 4) if per_student_dispersion else None
        ),
        "pct_pairs_vetoed": round(100 * n_vetoed_pairs / n_pairs, 2) if n_pairs else None,
        "pct_pairs_hard_floor": round(100 * n_hard_floor_pairs / n_pairs, 2) if n_pairs else None,
        "pct_pairs_no_opinion": round(100 * n_no_opinion_pairs / n_pairs, 2) if n_pairs else None,
        "coverage_mean": round(statistics.mean(coverage_vals), 4) if coverage_vals else None,
        "coverage_min": round(min(coverage_vals), 4) if coverage_vals else None,
        "coverage_max": round(max(coverage_vals), 4) if coverage_vals else None,
        "dealbreaker_students": db_total,
        "dealbreaker_buried_ok": db_buried_ok,
        "distinct_m_values": len({round(m, 4) for m in all_m}),
    }
    if dump:
        with open(_RESULTS_PATH, "w") as fh:
            json.dump(stats, fh, indent=2)
    return stats


def _pct(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    k = (len(xs) - 1) * (pct / 100.0)
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return xs[int(k)]
    return xs[lo] * (hi - k) + xs[hi] * (k - lo)


def print_stats() -> dict[str, Any]:
    """Run the full sim and print the aggregate stats (callable from a REPL)."""
    stats = run_matches()
    print(json.dumps(stats, indent=2))
    return stats


# ── Module-level fixtures shared by the tests (built once) ───────────────────

_STUDENTS = make_students(1000)
_SCHOOLS, _PROGRAMS = make_schools(50)
_STATS = run_matches(_STUDENTS, _PROGRAMS, dump=True)


# ── Invariant tests ──────────────────────────────────────────────────────────


def test_scale_shape():
    """1000 students, ~230 programs, every pair scored without exception."""
    assert _STATS["n_students"] == 1000
    assert 200 <= _STATS["n_programs"] <= 260
    assert _STATS["exceptions"] == 0
    assert _STATS["n_pairs"] == _STATS["n_students"] * _STATS["n_programs"]


def test_all_m_bounded_and_finite():
    """Chart 3: every M ∈ [0,1], no NaN/inf, across all 1000×~230 pairs."""
    for stu in _STUDENTS:
        ranked = rank_programs(stu, _PROGRAMS, cpef_enabled=True, include_eliminated=True)
        for prog, sc in ranked:
            m = float(sc.fitness)
            assert 0.0 <= m <= 1.0, f"M out of [0,1]: {m} for {prog.program_id}"
            assert not math.isnan(m) and not math.isinf(m)
            c = float(sc.confidence)
            assert 0.0 <= c <= 1.0 and not math.isnan(c)


def test_rankings_sorted_by_m_desc():
    """rank_programs returns programs sorted by M descending (tie-break confidence)."""
    for stu in _STUDENTS[::25]:  # every 25th student is plenty to prove the sort
        ranked = rank_programs(stu, _PROGRAMS, cpef_enabled=True, include_eliminated=True)
        ms = [float(sc.fitness) for _, sc in ranked]
        assert ms == sorted(ms, reverse=True)


def test_confirmed_dealbreaker_caps_value_at_epsilon_times_inner():
    """Chart 3 hardened floor — the invariant the code ACTUALLY guarantees today:
    a hard-floored (CONFIRMED deal-breaker) s→p value is capped at ``epsilon·inner``.

    This is the literal floor the implementation applies
    (``matching.cpef``: ``value = min(value, p['epsilon'] * inner)`` when ``hard``).
    Because the cap is *proportional to inner fit*, a confirmed deal-breaker with an
    otherwise-strong fit keeps a small-but-nonzero value — it is NOT slammed to a flat
    constant. See ``test_confirmed_dealbreaker_below_clean_of_comparable_fit`` for the
    place where the spec's "below EVERY clean program" wording does not hold.
    """
    eps = DEFAULT_PARAMS["epsilon"]
    checked = 0
    for stu in _STUDENTS:
        if not stu.sparse.get("_dealbreaker"):
            continue
        for prog in _PROGRAMS:
            sp_val, sp_bd = cpef(stu, prog)
            if not sp_bd.get("hard_floor"):
                continue
            checked += 1
            # ``inner`` in the breakdown is rounded to 4 dp, so allow a rounding-
            # sized slack (eps * 0.5e-4) on top of float noise.
            tol = eps * 0.5e-4 + 1e-9
            assert sp_val <= eps * sp_bd["inner"] + tol, (
                f"hard-floored s→p value {sp_val} exceeds epsilon*inner "
                f"{eps * sp_bd['inner']} for {prog.program_id}"
            )
    assert checked > 0, "expected confirmed-dealbreaker pairs to verify the floor"


def test_confirmed_dealbreaker_below_clean_of_comparable_fit():
    """Chart 3 — the hardened floor DOES bury a confirmed deal-breaker below a clean
    program *of comparable-or-better inner fit*. (This is the practically-meaningful
    promise; see the HONEST-NOTE test below for where the absolute wording breaks.)

    For each deal-breaker student we compare the best hard-floored program against the
    clean program whose inner fit is closest from above — the deal-breaker must lose.
    """
    checked = 0
    for stu in _STUDENTS:
        if not stu.sparse.get("_dealbreaker"):
            continue
        ranked = rank_programs(stu, _PROGRAMS, cpef_enabled=True, include_eliminated=True)
        hard = [
            (float(sc.fitness), sc.fitness_breakdown["inner"])
            for _, sc in ranked
            if sc.fitness_breakdown.get("hard_floor")
        ]
        clean = [
            (float(sc.fitness), sc.fitness_breakdown.get("inner", 0.0))
            for _, sc in ranked
            if not sc.fitness_breakdown.get("hard_floor")
        ]
        if not hard or not clean:
            continue
        for hm, h_inner in hard:
            # clean programs whose inner fit is at least the hard one's inner fit
            comparable = [cm for cm, c_inner in clean if c_inner >= h_inner - 1e-9]
            if comparable:
                checked += 1
                assert hm < max(comparable) + 1e-9, (
                    f"confirmed deal-breaker (M={hm}, inner={h_inner}) outranked a clean "
                    f"program of >= inner fit"
                )
    assert checked > 0, "expected comparable-fit comparisons to verify"


def test_honest_note_hardened_floor_is_proportional_to_inner():
    """HONEST FINDING (spec-vs-implementation gap), pinned as a passing test so it is
    not silently lost: the spec promises a CONFIRMED deal-breaker ranks BELOW *every*
    non-vetoed program. The implementation does NOT guarantee that absolute wording,
    because the hardened floor is ``value = min(value, epsilon · inner)`` — PROPORTIONAL
    to the program's OWN inner fit, not a flat constant.

    Consequence: among two confirmed deal-breakers, the one with the stronger inner fit
    keeps the higher M (``≈ (epsilon·inner)^alpha``). So a confirmed deal-breaker with a
    strong inner fit can still EXCEED a clean-but-softly-vetoed program whose inner is
    near zero. (This is the deliberate design tension the prior pass documented — the
    floor scales with inner instead of being absolute. NOT changed here.)

    This pins the MECHANISM directly (floor ∝ inner), which is robust to dataset shifts,
    rather than a specific population inversion that depends on a particular seed.

    Fix options for a future slice (NOT done here — this is a validation pass):
      • make the hard floor absolute (``value = epsilon`` or ``epsilon * prior``), or
      • bury any program once the cumulative veto product drops below a threshold,
        not only when a single dimension confirms at the epsilon floor.
    """
    eps = DEFAULT_PARAMS["epsilon"]
    # A student with a confirmed geo_avoid deal-breaker and a high-confidence profile
    # (so the veto is CONFIRMED for both programs below).
    stu = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_avoid": ["USA"],
            "interest_themes": ["data_science", "ai"],
            "gpa": 3.5,
            "field_of_study": "data_science",
        },
        extractor_quality=0.95,
        profile_completeness=0.9,
    )
    # Both hard-floored (all locations on the avoid list), differ only in inner fit:
    # strong = perfect theme overlap; weak = no theme overlap.
    strong = ProgramFeatures(
        program_id="hard_strong",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 20000,
            "interest_themes": ["data_science", "ai"],
        },
        data_completeness=0.9,
    )
    weak = ProgramFeatures(
        program_id="hard_weak",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 20000,
            "interest_themes": ["art_history"],
        },
        data_completeness=0.9,
    )
    v_strong, bd_strong = cpef(stu, strong)
    v_weak, bd_weak = cpef(stu, weak)
    assert bd_strong["hard_floor"] and bd_weak["hard_floor"], (bd_strong, bd_weak)
    # the floor is proportional to inner: stronger inner → strictly higher floored value
    assert bd_strong["inner"] > bd_weak["inner"], (bd_strong["inner"], bd_weak["inner"])
    assert v_strong > v_weak, (v_strong, v_weak)
    # each is exactly the proportional floor epsilon·inner (not a flat constant)
    assert abs(v_strong - eps * bd_strong["inner"]) < 1e-4, (v_strong, bd_strong["inner"])
    assert abs(v_weak - eps * bd_weak["inner"]) < 1e-4, (v_weak, bd_weak["inner"])


def test_immigration_status_never_enters_the_veto():
    """GAP 3 DEFERRED by fairness contract (Spec 38 §3/§9 + Spec 46 §6): immigration
    status must NEVER be a ranking/selection criterion. Even when a student carries an
    eligibility flag and a program states a sponsorship attribute, the matcher MUST NOT
    raise any such deal-breaker — eligibility is an operational feasibility readout
    (InternationalService), not a matcher input. Pinned here so a future attempt to wire
    it into the veto trips both this test and tests/test_spec38_fairness_contract.py."""
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "interest_themes": ["data_science", "ai"],
            # an upstream eligibility flag must be inert in the matcher:
            "visa_required": True,
            "gpa": 3.5,
            "field_of_study": "data_science",
        },
        extractor_quality=0.95,
        profile_completeness=0.9,
    )
    prog = ProgramFeatures(
        program_id="no_sponsor",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 25000,
            "interest_themes": ["data_science", "ai"],
            "sponsors_international": False,
        },
        data_completeness=0.9,
    )
    _, bd = cpef(student, prog)
    keys = {db["key"] for db in bd["dealbreakers"]}
    assert "visa" not in keys and "immigration" not in keys and "eligibility" not in keys, bd
    # and it is NOT hard-floored on an otherwise-clean, well-fit pair
    assert bd["hard_floor"] is False, bd


def test_degree_level_graded_signal_present_and_grades_adjacent():
    """GAP 4 — the graded degree-level fit signal is now part of the CPEF assembly:
    an EXACT level grades 1.0, an ADJACENT-acceptable level (masters↔doctoral /
    professional) grades 0.6 (not a clean pass), and it appears as a scored signal
    'degree_level' in the breakdown. The veto still buries a true wrong-family
    mismatch — this signal only adds graded nuance for the acceptable cases."""
    # exact: a student targeting masters at a masters program → degree_level f == 1.0
    exact_student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "degree_level_target": "masters",
            "interest_themes": ["data_science"],
            "gpa": 3.5,
        },
        extractor_quality=0.9,
    )
    masters_prog = ProgramFeatures(
        program_id="masters",
        sparse={"target_education_level": "masters", "interest_themes": ["data_science"]},
        data_completeness=0.9,
    )
    doctoral_prog = ProgramFeatures(
        program_id="doctoral",
        sparse={"target_education_level": "doctoral", "interest_themes": ["data_science"]},
        data_completeness=0.9,
    )
    _, bd_exact = cpef(exact_student, masters_prog)
    dl_exact = next(s for s in bd_exact["signals"] if s["key"] == "degree_level")
    assert dl_exact["f"] == 1.0, bd_exact

    # adjacent-acceptable: masters target at a doctoral program → graded 0.6 (NOT 1.0,
    # NOT vetoed — doctoral is a compatible reach for a bachelors holder)
    _, bd_adj = cpef(exact_student, doctoral_prog)
    dl_adj = next(s for s in bd_adj["signals"] if s["key"] == "degree_level")
    assert dl_adj["f"] == 0.6, bd_adj
    assert bd_adj["hard_floor"] is False, bd_adj


def test_degree_grade_lifts_exact_over_adjacent_all_else_equal():
    """GAP 4 — with everything else identical, an EXACT degree-level match scores higher
    than an ADJACENT-acceptable one, because the graded degree_level signal (1.0 vs 0.6)
    now contributes to the inner fit instead of both reading as a clean pass."""
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "degree_level_target": "masters",
            "interest_themes": ["data_science", "ai"],
            "gpa": 3.5,
        },
        extractor_quality=0.9,
    )
    themes = {"interest_themes": ["data_science", "ai"]}
    exact = ProgramFeatures(
        program_id="exact",
        sparse={"target_education_level": "masters", **themes},
        data_completeness=0.9,
    )
    adjacent = ProgramFeatures(
        program_id="adjacent",
        sparse={"target_education_level": "professional", **themes},
        data_completeness=0.9,
    )
    v_exact, _ = cpef(student, exact)
    v_adj, _ = cpef(student, adjacent)
    assert v_exact > v_adj, (v_exact, v_adj)


def test_no_preference_program_gives_neutral_p2s():
    """Chart 2: a program with NO ProgramPreference has 'no opinion' → p→s == 1.0."""
    no_pref = [p for p in _PROGRAMS if getattr(p, "_pref_kind", None) == "none"]
    assert no_pref, "sim should contain no-preference programs"
    for prog in no_pref[:50]:
        ps, bd = cpef_program_to_student(_STUDENTS[0], prog)
        assert ps == 1.0
        assert bd.get("no_prefs") is True


def test_preference_program_can_pull_m_down_but_not_bury():
    """Chart 2/3: a program that the student fails on its preferences pulls M down
    (p→s < 1) but is floored by ps_floor — it dents, doesn't bury."""
    # Build a deliberately picky program and a lenient twin, score the same student.
    base_sparse = {
        "target_education_level": "masters",
        "locations": ["USA"],
        "tuition_usd_per_year": 25000,
        "interest_themes": ["data_science"],
    }
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "budget_max_usd_per_year": 60000,
            "interest_themes": ["data_science"],
            "gpa": 3.0,
            "field_of_study": "data_science",
        },
        profile_completeness=0.8,
    )
    lenient = ProgramFeatures(program_id="lenient", sparse=dict(base_sparse))
    picky = ProgramFeatures(
        program_id="picky",
        sparse={
            **base_sparse,
            "pref_min_gpa": 3.95,
            "pref_fields": ["law"],
            "pref_levels": ["masters"],
        },
    )
    ps_picky, bd_picky = cpef_program_to_student(student, picky)
    assert ps_picky < 1.0
    assert ps_picky >= bd_picky["floor"]  # floored, never buried by the program gate
    m_lenient = float(rank_programs(student, [lenient], cpef_enabled=True)[0][1].fitness)
    m_picky = float(rank_programs(student, [picky], cpef_enabled=True)[0][1].fitness)
    assert m_picky < m_lenient


def test_ranking_key_excluded_from_math():
    """Chart 2: a program's 'ranking'/'weight_ranking' key never enters the score.
    Stripping it leaves M and the signal set byte-identical."""
    with_ranking = [p for p in _PROGRAMS if "ranking" in p.sparse]
    assert with_ranking, "sim should contain programs carrying a ranking key"
    stu = _STUDENTS[3]
    for prog in with_ranking[:30]:
        stripped = ProgramFeatures(
            program_id=prog.program_id,
            sparse={k: v for k, v in prog.sparse.items() if k not in ("ranking", "weight_ranking")},
            embedding=prog.embedding,
            data_completeness=prog.data_completeness,
        )
        m_full = float(rank_programs(stu, [prog], cpef_enabled=True)[0][1].fitness)
        m_strip = float(rank_programs(stu, [stripped], cpef_enabled=True)[0][1].fitness)
        assert m_full == m_strip, f"ranking key leaked into M for {prog.program_id}"
        # and it is not present as a scored signal
        bd = rank_programs(stu, [prog], cpef_enabled=True)[0][1].fitness_breakdown
        assert all(sig["key"] not in ("ranking", "weight_ranking") for sig in bd["signals"])


def test_m_not_degenerate():
    """Chart 3 coverage-damp / dispersion: M is not a constant. There is meaningful
    spread both across the whole population and within a single student's ranking."""
    assert _STATS["m_stdev"] is not None and _STATS["m_stdev"] > 0.02, _STATS["m_stdev"]
    assert _STATS["distinct_m_values"] > 50, _STATS["distinct_m_values"]
    # within-student spread (the coverage damp should make some programs clearly
    # better than others for a given student)
    assert _STATS["per_student_dispersion_mean"] > 0.01, _STATS["per_student_dispersion_mean"]


def test_coverage_damp_deeper_profile_sharper():
    """Chart 3 coverage damp: a deeper profile (more present signals → higher
    coverage) produces a sharper (more dispersed) ranking than a thin one."""
    thin = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "interest_themes": ["data_science"],
        },
        profile_completeness=0.3,
    )
    deep = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "budget_max_usd_per_year": 40000,
            "interest_themes": ["data_science", "ai"],
            "career_arcs": ["industry"],
            "values": ["impact"],
            "needs_signals": {"career_services": 0.8},
            "gpa": 3.5,
            "field_of_study": "data_science",
        },
        profile_completeness=0.9,
    )
    thin_ms = [float(sc.fitness) for _, sc in rank_programs(thin, _PROGRAMS, cpef_enabled=True)]
    deep_ms = [float(sc.fitness) for _, sc in rank_programs(deep, _PROGRAMS, cpef_enabled=True)]
    assert statistics.pstdev(deep_ms) > statistics.pstdev(thin_ms)


# ── Chart 1: enrichment planner sweep over 1000 varied signal-states ─────────


def test_planner_essentials_first_over_1000_states():
    """Chart 1: across 1000 varied signal-states, whenever an essential field is
    still actionable (ask/confirm), the planner's #1 pick is an essential."""
    states = make_signal_states(1000)
    checked = 0
    for state in states:
        plan = plan_next(state, limit=3)
        if not plan:
            continue
        # is any essential still actionable?
        essential_actionable = any(action_for(state.get(k)) != "skip" for k in ESSENTIAL_KEYS)
        if essential_actionable:
            checked += 1
            assert plan[0]["tier"] == "essential", (
                f"planner surfaced {plan[0]['tier']} '{plan[0]['field']}' "
                f"while an essential was still actionable"
            )
    assert checked > 100, f"expected many states with actionable essentials, got {checked}"


def test_planner_ask_before_confirm_within_tier():
    """Chart 1: within the surfaced plan, ASK (missing/weak) precedes CONFIRM
    (1-tap) when they share the top tier."""
    states = make_signal_states(500)
    for state in states:
        plan = plan_next(state, limit=8)
        # walk the plan; for any adjacent same-tier pair, ask must not follow confirm
        for a, b in zip(plan, plan[1:], strict=False):
            if a["tier"] == b["tier"]:
                assert not (a["action"] == "confirm" and b["action"] == "ask"), (
                    f"confirm precedes ask within tier {a['tier']}: {a['field']} → {b['field']}"
                )


def test_planner_skips_confirmed_and_never_asks_ranking():
    """Chart 1: confirmed (conf ≥ 0.85) fields are skipped; school 'ranking'
    importance is never in the catalog so it is never asked."""
    # ranking is structurally absent from the catalog
    assert all("ranking" not in f["key"] for f in CATALOG)
    # a fully-confirmed state yields an empty plan (everything skipped)
    confirmed_state = {
        f["key"]: {"value": "x", "confidence": 0.95, "source": "sim"} for f in CATALOG
    }
    assert plan_next(confirmed_state) == []
    assert essentials_present(confirmed_state) is True
    # and no plan over the sweep ever names a ranking field
    for state in make_signal_states(300):
        for entry in plan_next(state, limit=10):
            assert "ranking" not in entry["field"]


def test_essentials_present_gates_matching():
    """Chart 1↔3 handshake: essentials_present is the matching prerequisite.
    A state missing any essential is not match-ready; filling them flips it."""
    # start from confirmed-everything, then blank one essential at a time
    base = {f["key"]: {"value": "x", "confidence": 0.95} for f in CATALOG}
    assert essentials_present(base) is True
    for ek in ESSENTIAL_KEYS:
        broken = {k: dict(v) for k, v in base.items()}
        broken[ek] = {"value": None, "confidence": 0.95}
        assert essentials_present(broken) is False, f"missing essential {ek} should block matching"


# ── Confidence / two-sided-confidence honesty (Chart 2 / Chart 3) ────────────


def test_two_sided_confidence_is_live_and_varies_mean_rho():
    """GAP 1 — two-sided confidence is LIVE (Chart 3 'c = c_student × c_program /
    fit & confidence fused'). Per-signal confidence is now the product of the
    student's extractor_quality (Spec 1) and the program's data_completeness
    (Spec 2 authority precedence), so mean_rho VARIES across (student, program)
    pairs instead of collapsing to one Slice-A constant. This is the flip that
    proves the previously-inert confidence axis went live."""
    rhos = set()
    for stu in _STUDENTS[::50]:
        ranked = rank_programs(stu, _PROGRAMS[:5], cpef_enabled=True)
        for _, sc in ranked:
            rhos.add(sc.fitness_breakdown.get("mean_rho"))
    # confidence now varies with profile depth × program authority
    assert len(rhos) > 1, f"expected mean_rho to vary now confidence is live, got {sorted(rhos)}"
    # and every value is a valid gain in (0, 1)
    assert all(r is not None and 0.0 < r < 1.0 for r in rhos), sorted(rhos)


def test_extractor_quality_sharpens_inner_away_from_prior():
    """GAP 1 'fit & confidence FUSED / deeper profile sharper': for a FIXED program and
    a strong (above-prior) fit, raising the student's extractor_quality moves the fused
    posterior-mean ``inner`` strictly AWAY from the 0.5 prior (sharper), and the final
    coverage-damped value rises monotonically too. Verified end-to-end through cpef on a
    clean, un-vetoed pair (the live path, not just the helper)."""
    base_sparse = {
        "education_level": "bachelors",
        "interest_themes": ["data_science", "ai"],
        "career_arcs": ["industry"],
        "values": ["impact"],
        "gpa": 3.6,
        "field_of_study": "data_science",
    }
    prog = ProgramFeatures(
        program_id="clean_strong",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "interest_themes": ["data_science", "ai"],
            "career_arcs": ["industry"],
            "values": ["impact"],
        },
        data_completeness=0.9,  # claimed/high authority so c is dominated by the student side
    )
    prior = DEFAULT_PARAMS["prior"]
    inner_dists = []
    values = []
    for q in (0.2, 0.5, 0.85, 0.99):
        stu = StudentFeatures(sparse=dict(base_sparse), extractor_quality=q)
        v, bd = cpef(stu, prog)
        inner_dists.append(bd["inner"] - prior)  # strong fit → inner above prior
        values.append(v)
    # the fused posterior mean sharpens away from the prior as confidence rises
    assert all(b > a for a, b in zip(inner_dists, inner_dists[1:], strict=False)), inner_dists
    # and the coverage-damped value rises monotonically with confidence on a strong fit
    assert all(b > a for a, b in zip(values, values[1:], strict=False)), values


def test_lower_confidence_pulls_inner_toward_prior():
    """GAP 1 (the symmetric direction): on a WEAK (below-prior) fit, raising confidence
    pulls the fused ``inner`` further BELOW the prior, and lowering it relaxes ``inner``
    back toward 0.5 — confidence sharpens in whichever direction the raw fit points."""
    prior = DEFAULT_PARAMS["prior"]
    base_sparse = {
        "education_level": "bachelors",
        "interest_themes": ["art_history"],  # no overlap with the program → weak fit
        "gpa": 3.0,
    }
    prog = ProgramFeatures(
        program_id="weak",
        sparse={
            "target_education_level": "masters",
            "interest_themes": ["robotics"],
            "needs_signals": {},
        },
        data_completeness=0.9,
    )
    inners = []
    for q in (0.99, 0.5, 0.2):
        stu = StudentFeatures(sparse=dict(base_sparse), extractor_quality=q)
        _, bd = cpef(stu, prog)
        inners.append(bd["inner"])
    # as confidence drops, inner relaxes UP toward the prior (less sharp below it)
    assert all(b > a for a, b in zip(inners, inners[1:], strict=False)), inners
    assert inners[-1] <= prior + 1e-9, inners


# ── Per-type fit functions: boundary values + exception-safety (Spec 3 §3/§9) ──


def test_all_fit_functions_boundary_values():
    """Spec 3 §9 'each f_k type: boundary values (exact, far, disjoint, over-budget
    ramp)'. Exercises ALL eight per-type fit functions at their boundaries, including
    the five (categorical/numeric_target/boolean/degree_level/date) that the CPEF
    assembly does not yet route data through — so the graded behavior they will need
    when wired is pinned now."""
    # categorical: exact / curated-similar / disjoint / unknown→neutral
    assert _fits.fit_categorical("ds", "ds") == 1.0
    assert _fits.fit_categorical("ds", "stats", {("ds", "stats"): 0.8}) == 0.8
    assert _fits.fit_categorical("ds", "art_history") == 0.0
    assert _fits.fit_categorical(None, "ds") == 0.5
    # numeric_higher: at-mean=0.5, well-above→~1, well-below→~0
    assert abs(_fits.fit_numeric_higher(3.0, 3.0, 0.3) - 0.5) < 1e-9
    assert _fits.fit_numeric_higher(4.0, 3.0, 0.3) > 0.95
    assert _fits.fit_numeric_higher(2.0, 3.0, 0.3) < 0.05
    # numeric_target: exact=1, far→0
    assert abs(_fits.fit_numeric_target(24, 24, 6) - 1.0) < 1e-9
    assert _fits.fit_numeric_target(60, 24, 6) < 0.02
    # range (over-budget ramp): affordable=1, mid-overage in (0,1), far→0
    assert _fits.fit_range(30000, 35000) == 1.0
    assert 0.0 < _fits.fit_range(40000, 35000, 0.25) < 1.0
    assert _fits.fit_range(60000, 35000, 0.25) == 0.0
    # boolean: has=1, hard-want-miss=0, soft-want-miss=0.3
    assert _fits.fit_boolean(True) == 1.0
    assert _fits.fit_boolean(False, want_hard=True) == 0.0
    assert _fits.fit_boolean(False, want_hard=False) == 0.3
    # geo: overlap=1, disjoint=0, unknown→0.5
    assert _fits.fit_geo(["USA"], ["USA", "UK"]) == 1.0
    assert _fits.fit_geo(["UK"], ["USA"]) == 0.0
    assert _fits.fit_geo([], ["USA"]) == 0.5
    # degree_level: exact=1, adjacent-acceptable=0.6, wrong-family=0
    assert _fits.fit_degree_level("masters", "masters") == 1.0
    assert _fits.fit_degree_level("masters", "doctoral") == 0.6
    assert _fits.fit_degree_level("masters", "bachelors") == 0.0
    # date: comfortable=1, infeasible=0, shrinking→linear
    assert _fits.fit_date(120, 90) == 1.0
    assert _fits.fit_date(0, 90) == 0.0
    assert abs(_fits.fit_date(45, 90) - 0.5) < 1e-9


def test_fit_functions_never_raise_on_out_of_domain_numbers():
    """Robustness regression (group invariant 'no exception over all pairs'): a
    corrupt out-of-domain numeric signal from an upstream extractor must NOT raise
    OverflowError out of a fit function — it must saturate to a bounded fit. This
    pins the fits.py exponent-clamp fix; before it, fit_numeric_higher(gpa<-122) and
    fit_numeric_target(|x|~1e200) raised OverflowError that propagated out of cpef →
    rank_programs and crashed the whole ranking."""
    extremes = [-1e308, -1e200, -1e6, -122.0, 1e6, 1e200, 1e308, float("inf"), float("-inf")]
    for x in extremes:
        h = _fits.fit_numeric_higher(x, 3.0, 0.3)
        assert 0.0 <= h <= 1.0 and not math.isnan(h), f"fit_numeric_higher({x}) = {h}"
        t = _fits.fit_numeric_target(x, 0.0, 0.5)
        assert 0.0 <= t <= 1.0 and not math.isnan(t), f"fit_numeric_target({x}) = {t}"
    # the saturated direction is still correct: far-below the mean → ~0, far-above → ~1
    assert _fits.fit_numeric_higher(-1e6, 3.0, 0.3) < 1e-6
    assert _fits.fit_numeric_higher(1e6, 3.0, 0.3) > 1.0 - 1e-6


def test_no_exception_under_adversarial_numeric_signals_end_to_end():
    """End-to-end: feed extreme/corrupt numeric values (gpa, budget, tuition,
    pref_min_gpa) through the full CPEF rank and assert ZERO exceptions and every M
    bounded. This is the scale form of the 'no exception over all pairs' invariant
    against unvalidated upstream data (the overflow class the validator hit 12,816×)."""
    rng = random.Random(99)
    bad_numbers = [-1e308, -1e200, -1e6, -150.0, 0.0, 1e6, 1e200, 1e308, float("inf"), float("nan")]
    students: list[StudentFeatures] = []
    for _ in range(200):
        students.append(
            StudentFeatures(
                sparse={
                    "education_level": "bachelors",
                    "budget_max_usd_per_year": rng.choice(bad_numbers),
                    "needs_aid": False,
                    "interest_themes": ["ai"],
                    "gpa": rng.choice(bad_numbers),
                    "field_of_study": "data_science",
                }
            )
        )
    progs: list[ProgramFeatures] = []
    for k in range(20):
        progs.append(
            ProgramFeatures(
                program_id=f"adv_{k}",
                sparse={
                    "target_education_level": "masters",
                    "locations": ["USA"],
                    "tuition_usd_per_year": rng.choice(bad_numbers),
                    "interest_themes": ["ai"],
                    "pref_min_gpa": rng.choice(bad_numbers),
                    "pref_fields": ["data_science"],
                    "pref_levels": ["bachelors"],
                },
            )
        )
    for stu in students:
        ranked = rank_programs(stu, progs, cpef_enabled=True, include_eliminated=True)
        for _, sc in ranked:
            m = float(sc.fitness)
            assert 0.0 <= m <= 1.0 and not math.isnan(m) and not math.isinf(m)


# ── Float-boundary budget veto (deal-breaker hard floor) ─────────────────────


def test_budget_veto_hard_floor_trips_at_analytic_epsilon_boundary():
    """Regression for the float-boundary deal-breaker bug: a confirmed ~1.5x-over-
    budget program whose analytic veto ``v`` lands EXACTLY at ``epsilon`` must still
    trip the hard floor (it was escaping when float made v = 0.010000000000000009 >
    epsilon). Budget 40000 → ceiling 50000, span 10000; tuition 59900 → analytic
    v = 1 - 9900/10000 = 0.01 = epsilon."""
    stu = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "budget_max_usd_per_year": 40000,
            "needs_aid": False,
            "interest_themes": ["ai"],
        }
    )
    boundary = ProgramFeatures(
        program_id="boundary",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 59900,
            "interest_themes": ["ai"],
        },
    )
    _, bd = cpef(stu, boundary)
    assert bd["hard_floor"] is True, "confirmed over-budget at the epsilon boundary must bury"
    # a program just over the soft ceiling (within the linear ramp) stays SOFT
    soft = ProgramFeatures(
        program_id="soft",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 50001,
            "interest_themes": ["ai"],
        },
    )
    _, bd_soft = cpef(stu, soft)
    assert bd_soft["hard_floor"] is False, "a mild overage in the ramp must only dent, not bury"


# ── Confidence ↔ fit fusion: posterior-mean monotonicity (Chart 3, Spec 3 §5) ──


def test_confidence_monotonicity_moves_fit_away_from_prior():
    """The defining Chart-3 property ('fit & confidence FUSED'): for a FIXED raw fit
    f, raising the per-signal confidence c moves the posterior-mean fhat AWAY from the
    0.5 prior (sharper), lowering it moves fhat TOWARD the prior. Tested directly on
    the posterior-mean math (fhat = f·rho + (1-rho)·prior with rho = confidence_to_gain(c))
    because the live cpef() pins c at the Slice-A constant. This is the formula the §5
    worked drop (imported→inferred) relies on."""
    prior = DEFAULT_PARAMS["prior"]
    cs = [0.1, 0.3, 0.5, 0.7, 0.9, 0.99]
    for f in (0.9, 0.7, 0.3, 0.1):  # both above and below the prior
        dists = []
        for c in cs:
            rho = confidence_to_gain(c)
            fhat = f * rho + (1.0 - rho) * prior
            dists.append(abs(fhat - prior))
        # strictly increasing |fhat - prior| as confidence rises
        assert all(b > a for a, b in zip(dists, dists[1:], strict=False)), (
            f"|fhat-prior| not monotone-increasing in c for f={f}: {dists}"
        )
    # f == prior is a fixed point: confidence cannot manufacture a direction
    for c in cs:
        rho = confidence_to_gain(c)
        fhat = prior * rho + (1.0 - rho) * prior
        assert abs(fhat - prior) < 1e-12


def test_claimed_outscores_derived_outscores_crawler():
    """GAP 1 / Chart 2 ('claimed program outweighs derived/crawler'): three programs
    identical in every fit dimension but differing in data_completeness (claimed 0.9 /
    derived 0.5 / crawler 0.4) now produce DISTINCT CPEF + M, and they order
    claimed > derived > crawler — a higher-authority program with the SAME fit lands a
    sharper (further-from-prior) score. This is the live behavior the Slice-A placeholder
    used to suppress."""
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "interest_themes": ["data_science", "ai"],
            "career_arcs": ["industry"],
            "values": ["impact"],
            "gpa": 3.5,
            "field_of_study": "data_science",
        },
        profile_completeness=0.9,
        extractor_quality=0.9,
    )
    # A clean, strong-fit program (above the 0.5 prior) so higher authority → higher M.
    base = {
        "target_education_level": "masters",
        "locations": ["USA"],
        "tuition_usd_per_year": 30000,
        "interest_themes": ["data_science", "ai"],
        "career_arcs": ["industry"],
        "values": ["impact"],
    }
    by_kind: dict[str, float] = {}
    for kind, dc in (("claimed", 0.9), ("derived", 0.5), ("crawler", 0.4)):
        prog = ProgramFeatures(program_id=f"p_{kind}", sparse=dict(base), data_completeness=dc)
        m, _ = mutual_match(student, prog)
        by_kind[kind] = m
    # all distinct
    assert len({round(v, 10) for v in by_kind.values()}) == 3, by_kind
    # and ordered by authority on a strong (above-prior) fit
    assert by_kind["claimed"] > by_kind["derived"] > by_kind["crawler"], by_kind


def test_claimed_preference_moves_m_more_than_derived_p2s():
    """GAP 1 (p→s direction) — a CLAIMED program preference the student fails on pulls M
    down MORE than a DERIVED one with the identical preference. The program-side
    authority (data_completeness) gates the satisfaction multiplier, so a confident
    (claimed) 'we want a different applicant' bites harder than a soft (derived) one."""
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "interest_themes": ["data_science"],
            "gpa": 3.0,
            "field_of_study": "data_science",
        },
        extractor_quality=0.85,
    )
    # identical, picky preferences the student fails; differ only in authority. The
    # program's themes do NOT match the student's, so the s→p inner stays near/below
    # the prior — that keeps the p→s satisfaction gate (the part GAP 1 changed) the
    # dominant lever, isolating the claimed-vs-derived effect on M.
    pref_sparse = {
        "target_education_level": "masters",
        "interest_themes": ["art_history"],
        "pref_min_gpa": 3.95,
        "pref_fields": ["law"],
        "pref_levels": ["masters"],
    }
    claimed = ProgramFeatures(program_id="claimed", sparse=dict(pref_sparse), data_completeness=0.9)
    derived = ProgramFeatures(program_id="derived", sparse=dict(pref_sparse), data_completeness=0.5)
    ps_claimed, bd_c = cpef_program_to_student(student, claimed)
    ps_derived, bd_d = cpef_program_to_student(student, derived)
    # a claimed rejection satisfaction is LOWER (pulls harder) than a derived one
    assert ps_claimed < ps_derived, (bd_c, bd_d)
    # …which makes the claimed program's M lower (more buried by its own pickiness).
    m_claimed, _ = mutual_match(student, claimed)
    m_derived, _ = mutual_match(student, derived)
    assert m_claimed < m_derived, (m_claimed, m_derived)


# ── Mutual-fit blend identities (Chart 3, Spec 3 §4) ──────────────────────────


def test_mutual_blend_identities_alpha_extremes_and_p2s_monotone():
    """Spec 3 §4 'Blend' identities: alpha=1 → M == CPEF_s→p (one-directional);
    alpha=0.5 → M == geometric mean √(sp·ps); and lowering CPEF_p→s lowers M with
    s→p fixed (a pickier program the student fails on its preferences pulls M down)."""
    student = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "budget_max_usd_per_year": 60000,
            "interest_themes": ["data_science"],
            "gpa": 3.0,
            "field_of_study": "data_science",
        },
        profile_completeness=0.8,
    )
    base = {
        "target_education_level": "masters",
        "locations": ["USA"],
        "tuition_usd_per_year": 25000,
        "interest_themes": ["data_science"],
    }
    lenient = ProgramFeatures(program_id="lenient", sparse=dict(base))
    picky = ProgramFeatures(
        program_id="picky",
        sparse={**base, "pref_min_gpa": 3.95, "pref_fields": ["law"], "pref_levels": ["masters"]},
    )
    sp, _ = cpef(student, picky)
    ps, _ = cpef_program_to_student(student, picky)

    # alpha = 1 → purely student-directional
    params1 = {**DEFAULT_PARAMS, "alpha": 1.0}
    m1, _ = mutual_match(student, picky, params=params1)
    assert abs(m1 - sp) < 1e-9, f"alpha=1 must equal s→p: M={m1} sp={sp}"

    # alpha = 0.5 → geometric mean
    params_half = {**DEFAULT_PARAMS, "alpha": 0.5}
    m_half, _ = mutual_match(student, picky, params=params_half)
    assert abs(m_half - (sp * ps) ** 0.5) < 1e-9, "alpha=0.5 must be √(sp·ps)"

    # lowering p→s (pickier program the student fails) lowers M with s→p held
    m_lenient, _ = mutual_match(student, lenient)
    m_picky, _ = mutual_match(student, picky)
    ps_lenient, _ = cpef_program_to_student(student, lenient)
    assert ps_lenient > ps  # lenient (no prefs) → 1.0 > picky's satisfaction
    assert m_picky < m_lenient, "a program the student fails on its prefs must pull M down"


def test_tiebreak_secondary_key_is_confidence_and_now_varies():
    """HONEST NOTE pinned (Spec 3 §4 vs implementation): the spec mandates ties on M
    break by coverage (ΣA_k) then raw fit (Σf_k). rank_programs' actual sort key is
    (M, confidence=mean_rho). With GAP 1 two-sided confidence live, mean_rho now VARIES
    (it tracks profile depth × program authority), so the secondary key is an ACTIVE
    tie-break — confidence, not the §4 coverage/raw-fit pair. This pins that the
    secondary key is confidence and is no longer inert; a future slice implementing the
    §4 coverage/raw-fit tie-break will surface here."""
    rhos = set()
    for stu in _STUDENTS[::100]:
        for _, sc in rank_programs(stu, _PROGRAMS[:8], cpef_enabled=True):
            rhos.add(round(float(sc.confidence), 6))
    # the secondary sort key (confidence = mean_rho) now varies → active tie-break
    assert len(rhos) > 1, f"confidence tie-break is unexpectedly constant: {sorted(rhos)}"
    assert all(0.0 < r < 1.0 for r in rhos), sorted(rhos)
