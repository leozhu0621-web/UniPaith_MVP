# AI Structure Build — Implementation Plan (master)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Build the three-part AI Structure (Spec 1 enrich · Spec 2 school/program · Spec 3 match) full-stack, plus turn the crawler data map (chart 4) into an autonomous routine skill.

**Architecture:** Deterministic Python matcher (no LLM in the score). Backend extraction/quantification + crawler reading on **Qwen** (Qwen2.5-VL-7B + Qwen2.5-7B via the existing `QwenProvider`/`ai/boundary.py`, vLLM). Human-facing language (rationale sentence, conversational Ask) stays **Claude**. Frontend on the existing React 19/TS stack.

**Tech Stack:** FastAPI · SQLAlchemy 2 async · Postgres 16/pgvector · Alembic · React 19/Vite/Zustand/TanStack Query · Qwen (vLLM) · Anthropic SDK.

**Specs:** `docs/superpowers/specs/2026-06-17-ai-structure-{1,2,3}-*.md`.

---

## Build order — shippable, independently-verifiable slices

Each slice ships green (tsc 0 · pytest green · build 0) and merges to `main` before the next.

| Slice | Spec | What ships | Depends on |
|---|---|---|---|
| **A** | 3 | CPEF matching core (one-directional `s→p`): per-type fits, two-sided-ready confidence shrinkage, in-formula veto, coverage damp; replaces `matching.py::score()`; persists into `fitness_score`; explainable breakdown; NDCG calibrated | — |
| **B** | 3 + 2 | `ProgramPreference` model + `c_program` authority confidence + `p→s` direction + **M blend** (α≈0.7) + sort by M | A |
| **C** | 1 | `enrichment_planner` + `GET /me/enrichment/next` + `POST /me/enrichment/{field}/value` + confidence/provenance stamping audit + frontend enrich widget | A |
| **D** | 2 | claim model + `POST /institutions/me/claims` + crawler no-op-on-claimed guard + `ProgramPreference` editor UI + wire format/outcomes/selectivity into the matcher | B |
| **E** | 2 + chart 4 | re-enable crawler write-path (Qwen extraction, grounded-never-invents) + populate typed outcome/admissions tables + derived target-applicant + **autonomous enrichment skill + instructions** (like the existing improve-enrichment runs) | D |

Each of B–E gets its own detailed plan file (`2026-06-17-ai-structure-build-slice-{b,c,d,e}.md`) authored when reached. **Slice A is detailed below.**

---

## File map (whole build)

**Backend**
- `services/matching.py` — rewrite `score()` → CPEF; add `cpef()`; generalize `_renormalized_weights`. (Slice A)
- `services/match/fits.py` *(new)* — per-type fit functions. (Slice A)
- `services/match/params.py` *(new)* — `DEFAULT_PARAMS`. (Slice A)
- `services/match_service.py` — sort by CPEF/M; persist scores; band unchanged. (A/B)
- `services/program_features.py` — per-(program,dim) priors; project new attributes. (A/D)
- `models/student.py` — `ProgramPreference`? no — program side. `models/institution.py` — `ProgramPreference`, claim fields. (B/D)
- `services/enrichment_planner.py` *(new)* + `api/enrichment.py` *(new)*. (C)
- `services/claim_service.py` *(new)* + claim endpoints in `api/institutions.py`. (D)
- `services/crawler/*` — restore write-path; `derive_preferences.py` *(new)*. (E)
- `ai/extraction_qwen.py` *(new or extend existing extractor)* — Qwen vision/text extraction. (E)

**Frontend**
- `pages/student/.../EnrichWidget.tsx` *(new)* — render-by-type enrich card (reuses `AnswerChoices`). (C)
- `api/enrichment.ts` *(new)*. (C)
- institution `ProgramPreferenceEditor.tsx` *(new)* + claim UI. (D)

**Autonomous routine (chart 4)**
- `.claude/skills/enrich-program-profiles/SKILL.md` *(new)* + supporting instructions. (E)

---

## SLICE A — CPEF matching core (detailed)

**Outcome:** `matching.py` computes one CPEF number per (student, program) that fuses fit and confidence, with in-formula deal-breaker veto and coverage damp, replacing the binary `rule_pass→0` + separate geometric-mean confidence. One-directional (`s→p`) for now; the M blend lands in Slice B. Persisted into `fitness_score` (+ legacy `match_score`); `confidence_score` = A-weighted mean of ρ (derived readout). NDCG@10 ≥ current baseline.

**Current signatures (grounded, `services/matching.py`):** `StudentFeatures{sparse, embedding, profile_completeness, extractor_quality}`, `ProgramFeatures{program_id, sparse, embedding, data_completeness}`, `Score{fitness, confidence, eliminated, fitness_breakdown, confidence_breakdown}`, `rule_pass`, `_education_compat`, `cosine/soft_align/needs_match`, `_renormalized_weights`, `score`, `rank_programs`. CPEF builds on these; `cosine`/`soft_align`/`needs_match` are retained as *fit components feeding `f_k`* (semantic fit), not as the top-level convex sum.

### Task A1 — `DEFAULT_PARAMS` + params module
**Files:** Create `unipaith-backend/src/unipaith/services/match/__init__.py`, `services/match/params.py`; Test `tests/test_cpef_params.py`.
- [ ] Define `DEFAULT_PARAMS = {"kappa":1.0, "tau0":1.0, "delta":0.25, "epsilon":0.01, "h":0.5, "logit_slope":1.7, "w_base":6.0, "n0":3.0, "alpha":0.7, "prior":0.5}`.
- [ ] Helper `confidence_to_gain(c, params)` → ρ = c (with τ0=κ); clamp c to [0.01,0.99]; test ρ(0.9)=0.9, ρ(0.4)=0.4, ρ(1.0)→0.99 clamp.
- [ ] Helper `two_sided_confidence(c_self, c_other)` → `c_self*c_other`; test 0.9×0.6=0.54.

### Task A2 — per-type fit functions
**Files:** Create `services/match/fits.py`; Test `tests/test_cpef_fits.py`.
- [ ] `fit_categorical(student_val, program_val, sim_table)` → 1 exact / sim / 0.
- [ ] `fit_numeric_higher(x, mu, sigma, slope)` → `1/(1+exp(-slope*(x-mu)/sigma))`; test median→0.5, +2σ→~1, −2σ→~0.
- [ ] `fit_numeric_target(x, target, h)` → `exp(-((x-target)/h)**2)`; test exact→1.
- [ ] `fit_range(value, lo, hi, delta)` → 1 inside; ramp over `delta*hi`; 0 beyond; test affordable→1, 14%-over (δ=.25)→0.44.
- [ ] `fit_boolean(has, want_hard)` → 1 / floor(0.0|0.3).
- [ ] `fit_geo(pref_set, prog_set)` → 1 / partial / 0.
- [ ] `fit_degree_level(student_level, program_level)` → 1 / 0.6 adjacency / 0 (veto handles wrong-family).
- [ ] `fit_date(margin_days, horizon_days)` → 1 / linear decay / 0.
- [ ] One test per function covering exact / mid / fail.

### Task A3 — shrinkage, attention, renormalized aggregate
**Files:** Modify `services/matching.py`; Test `tests/test_cpef_aggregate.py`.
- [ ] `posterior_fit(f, rho, prior)` → `rho*f + (1-rho)*prior`; test confirmed-perfect→~f, inferred-perfect→toward prior.
- [ ] `attention(w, rho)` → `(w/10)*rho`.
- [ ] Generalize `_renormalized_weights` usage into `aggregate(signals)` = `Σ A·f̂ / Σ A` over present signals; empty → `prior`. Test missing signal drops from both sums (no phantom zero — the 0.55-cap regression).

### Task A4 — confidence-aware veto + hardened floor
**Files:** Modify `services/matching.py`; Test `tests/test_cpef_veto.py`.
- [ ] `veto(dealbreakers)` = Π `(1 - rho_d*(1-v_d))`; `v_d∈[ε,1]`.
- [ ] Deal-breakers from existing signals: degree via `_education_compat` (incompatible→v=ε, adjacent→0.6, ok→1), visa via `StudentVisaInfo` (ineligible→ε, risky→0.3–0.7, ok→1), cost ramp beyond budget tolerance.
- [ ] Hardened-floor: any *confirmed* (ρ_d≥0.85) deal-breaker forces final CPEF strictly below the minimum un-vetoed score. Test: confirmed visa-ineligible → buried below every clean program; inferred → graded penalty.

### Task A5 — coverage damp + `cpef()` assembly
**Files:** Modify `services/matching.py`; Test `tests/test_cpef_score.py`.
- [ ] `coverage(present_A_sum, full_w_sum, n0)` = `(n0+ΣA)/(n0+Σw/10)`; ∈(0,1]; =1 only all-present-confirmed.
- [ ] `cpef(student, program, *, params, direction="s2p")` → `coverage * veto * aggregate`; returns `(value, breakdown)` with per-signal `f,c,rho,fhat,A`, each `v_d`, `g`. Worked-example test from Spec 3 §5 (≈0.584 inner; confidence-drop → 0.524).
- [ ] Build the per-signal list from `StudentFeatures.sparse` + `ProgramFeatures.sparse`: map preference weights → fit dims (cost→range, location→geo, outcomes→numeric_higher, flexibility→boolean, support→needs, time→numeric_target); structural (degree, GPA, field) get `w_base`. **Do not read ranking.**

### Task A6 — back-compat `score()` + `rank_programs`
**Files:** Modify `services/matching.py`, `services/match_service.py`; Test `tests/test_matching.py` (existing — keep green).
- [ ] Rewrite `score()` to call `cpef()`: `fitness = cpef value`; `confidence = A-weighted mean of ρ`; `eliminated = False` always (vetoed programs sink, never dropped); breakdown carries the CPEF dict. Keep return type `Score`.
- [ ] `rank_programs` sort key → `(float(score.fitness),)` with tie-break `(coverage, raw Σf)`; `include_eliminated` retained but nothing is eliminated now.
- [ ] `match_service`: persist `fitness_score = match_score = cpef`; `confidence_score = mean ρ`; keep `_fitness_band` (0.75/0.55/0.40).

### Task A7 — NDCG calibration + regression
**Files:** Test `tests/test_matching_ndcg.py` (existing eval harness if present, else add).
- [ ] Run the NDCG@10 eval; tune `DEFAULT_PARAMS` if below the pre-change baseline. Record the number in the commit.
- [ ] Full backend suite green; commit + ship Slice A to `main`.

### Slice A verification gate
`cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_cpef_*.py tests/test_matching*.py -q` green · ruff clean · NDCG@10 ≥ baseline · merged to main.

---

## Self-review (master)
- **Spec coverage:** Spec 1 → Slice C; Spec 2 → Slices D+E (model in B); Spec 3 → Slices A+B; chart 4 routine → Slice E. ✓
- **No silent caps:** CPEF removes the 0.55 cap (A3) — the existing matcher bug. ✓
- **Consistency:** CPEF symbols match Spec 3 §2; `c_program` deferred to B (defaults to 1.0/existing in A so A is self-contained). ✓
- **Ranking excluded:** asserted in A5 + a grep guard test in B. ✓
