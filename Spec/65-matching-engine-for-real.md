# 65 · Matching Engine, For Real — Compute the Dual Score

> The matching engine is the product. The papers describe it precisely: *"the LLMs convert the user's context into prompts and feature vectors. The ML engine converts those into matching recommendations using **collaborative filtering, pattern recognition, and other ML techniques**. LLMs present ML's outcomes with adequate reasoning"* (`Master Paper`:67), producing per-program **Fitness Level and Confidence Level** (`Master Paper`:57). What ships today is none of that: a hand-tuned weighted sum whose **0.45 embedding term is dead** (no vectors reach `cosine()`, `matching.py:277` → `0.0`), whose **program-side features are empty** (reads `Program.feature_vector_sparse`, a column that does not exist, `program_features.py:176`), and whose **Confidence is two-thirds frozen constants** (`matching.py:72,292`). This spec makes the score real.
>
> The shape is right — `matching.py` is a clean, explainable scorer with the correct seam (`63`: ML computes, Claude explains). The work is to **fill the seam with a real ML signal**: write the embeddings the cosine term needs, build the program feature vectors the tag/needs terms need, add the collaborative-filtering signal the papers name, and define Fitness and Confidence as two genuinely separable quantities — then prove match quality with the eval gate that `matching.py:53` promises and never implemented.
>
> Build anchor: extend `services/matching.py`, `services/program_features.py`, `services/match_service.py`, `services/ml_state.py`, and the dormant `embeddings`/`student_feature_vectors` (`Vector(1536)`) tables. Pairs with `63` (ML boundary), `67` (learning loop feeds the weights), `66` (institution side), `68` (real data to embed), `62` (eval), `46` §6 (fairness gate).
>
> Status: **draft v1.0** · 2026-06-02 · turns the dead heuristic into a wired embedding + CF + dual-score engine with a real eval gate. Rule-based path stays the fallback (`tests/test_plan2_integration.py`).

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Explainable component scorer (cosine/soft/needs) | `matching.py:259` `score()` | exists — keep |
| Hard-filter rule layer (education/geo/budget) | `matching.py:101` `rule_pass()` | exists — keep |
| Student embedding into the score | `matching.py:277` (always `None`→0) | **NEW (build): write + pass student embedding** |
| Program embedding into the score | not written; ANN table unused | **NEW (build): program embedder + pgvector ANN** |
| Program sparse features (interest/career/values/support) | `program_features.py:176` reads a phantom column | **NEW (build): `program_feature_vectors` + featurizer** |
| Collaborative filtering | `implicit` declared, imported nowhere | **NEW (build): implicit-feedback CF signal** |
| Fitness definition | weighted sum of 3 terms, 0.45 dead | exists — **redefine + extend** |
| Confidence definition | geo-mean, 2 frozen constants | exists — **redefine: real factors** |
| Learned rerank | `reranker.py` `IdentityReranker` (cold-start) | exists — activated by `67` |
| Match-quality eval (NDCG/p@k) | claimed `matching.py:53`, **no impl** | **NEW (build): rated golden set + `62` gate** |
| Rationale ("why this match") | `ai/rationale.py` Claude, grounded | exists — now explains a *real* score |

## 2. Embeddings — make the 0.45 term fire (start here)

The single highest-leverage fix. Per `63` §8, Qwen3-Embedding via Matryoshka emits exactly **1536 dims** to match the existing `Vector(1536)` columns — **no migration, no re-embed.** Start with a managed embedder (Bedrock/Voyage/Qwen-hosted) behind `04`; self-host on volume.

- **Program embedding (offline job).** Embed a normalized program document — overview + tracks + outcomes summary (`68`) + admissions profile + school context — into `embeddings` (entity_type=`program`, `Vector(1536)`), HNSW-indexed (`models/matching.py:119`). Recompute on program-version bump (mirror the rationale cache key).
- **Student embedding (inline/cached).** Embed the student's profile + goals + needs narrative into `student_feature_vectors.embedding`. Recompute on profile-version bump.
- **Candidate generation.** Replace the "score every program" loop with **pgvector ANN top-K** over program embeddings as stage-1 retrieval, then rule-filter, then score. This is the only way the catalog scales past a demo (`56` hybrid retrieval is the search analog; share the index).
- **Wire it through.** `_recompute_catalog_matches` (`api/students.py:965`) and `compute_matches_for_student` (`match_service.py:241`) must **pass `program_embeddings` and the student embedding** into `score()`. The cosine term stops being structurally zero. Gate the embedding path behind **`ai_matching_v2_enabled`** (net-new flag — there is none today); rule-based default until `62` shows a win.

## 3. Program feature vectors — fill the empty side

`program_features.py:176` reads `Program.feature_vector_sparse`; **that column was never created**, so `soft_align` and `needs_match` see `{}`/`[]` for every program and contribute near-nothing. Build the real thing:

- **New table `program_feature_vectors`** (parallels `student_feature_vectors`): `program_id` FK, `sparse_features` JSONB (`interest_themes`, `career_arcs`, `values`, `support_signals`, `social_features` — the exact vocabulary `matching.py:184-232` already expects), `embedding Vector(1536)`, `data_completeness` float, `program_version`, provenance + timestamps. Migration: Alembic, expand→contract, single head.
- **Featurizer (offline, Qwen per `63` §2.4 / rule-based fallback).** Extract the sparse vocabulary from program text + structured fields (`68`); same taxonomy as the student signals (`42`). Without this, the matcher's two structured terms are dead weight. The featurizer is eval-gated (`62`) and source-grounded (no invented themes).
- **`data_completeness` becomes real** — fraction of the feature vocabulary actually populated for this program — replacing the `0.5` cold-start default (`matching.py:84`) and feeding Confidence (§5).

## 3.5. Collaborative filtering — the signal the papers name

The papers name CF explicitly (`Master Paper`:67); `implicit` is in `pyproject.toml` and used nowhere. Build an **implicit-feedback CF signal** over the real interaction graph already captured (`saved_list_items`, `applications`, compares, `enrollment_records`, `attribution_events` `28`): student↔program implicit ratings → ALS/BPR factors (`implicit`) → a CF affinity score per (student, program). Blend as a fourth fitness term, **weight 0 until enough interactions exist** (cold-start → content/embeddings carry it; `67` learns the weight up). Train under `67`'s loop; never on `consent.training=false` data (`46` §9).

## 4. Fitness — define it

**Fitness = predicted holistic fit of this program for this student**, in [0,1], a blend (weights start hand-tuned, become learned via `67`):

```
fitness = w_sem·semantic(embeddings)      # §2  — replaces the dead cosine
        + w_tag·structured(soft_align)    # §3  — now non-empty
        + w_needs·needs_coverage          # existing, now with real program supports
        + w_cf·collaborative(§3.5)        # NEW, cold-start weight 0
        + w_feas·admit_feasibility(68/70) # NEW — can the student realistically get in
```

- **Fitness is not admit-probability.** Feasibility is *one* term; a long-shot dream program can be high-fitness, low-feasibility (→ "stretch" band, §6). Probability bands proper live in `70`.
- Weights sum to 1, exposed in `fitness_breakdown` (already the pattern, `matching.py:301`) so the rationale agent and the UI can show *what drove it*. Per-component sub-scores stay inspectable.
- Bias-avoidance: protected/proxy attributes never enter fitness (`46` §6); the feasibility term uses academic fit, not demographics. Fairness-gated before any learned weight ships.

## 5. Confidence — define it (kill the frozen constants)

**Confidence = how much to trust this Fitness**, orthogonal to it (papers: low-fitness + high-confidence = *"clearly not for you"*, `matching.py:40`). Geometric mean of **real** factors — the two frozen constants are the bug:

```
confidence = ( data_sufficiency · model_certainty ) ** ...
  data_sufficiency = profile_completeness · program_data_completeness(§3) · extractor_quality
  model_certainty  = calibration(67) · (1 − prediction_variance) · in_distribution
```

- **`extractor_quality` becomes real** — derived from the discovery extractor's per-turn confidence (`discovery_messages.extracted_signals`) instead of the hardcoded `0.85` (`matching.py:72`).
- **`extrapolation` (the `1.0` at `matching.py:292`) becomes `in_distribution`** — how far this student/program sits from the data the model was fit on (`67` provides it; cold-start = honest-low, not `1.0`).
- **Calibration** comes from `confidence_calibrator.py` once `67` fits it (today identity, permanent cold-start). Until then Confidence flows uncalibrated and **says so** — truthful low confidence beats false precision (`64` §7).

## 6. Bands, ranking & rerank

- **Bands** best-fit / stretch / safer (`Business Methodology`:70) derive from **fitness × feasibility**, not fitness alone: high-fit + high-feasibility = best-fit; high-fit + low-feasibility = stretch; moderate-fit + high-feasibility = safer. Banding logic is deterministic and testable.
- **Three-stage pipeline:** ANN candidate-gen (§2) → component scoring (§4/§5) → optional **learned rerank** (`reranker.py`, activated by `67`; `IdentityReranker` until then). Pagination on the ranked list (`73` adds cursor paging; today `limit`-only, `match_service.py:353`).
- Re-run on input edits is already the contract (`Business Methodology`:78); keep it cheap via the version-keyed caches.

## 7. Prove it — the eval gate that never existed

`matching.py:53` promises *"NDCG@10 ≥ 0.65 against 100 internally-rated pairs"* with **no rated set and no eval.** Build it:

- **Rated golden set** — ≥200 (student, program) pairs with expert relevance grades, stored as `eval_cases` (`62` §schema), spanning fields/levels/constraints; expand over time from real outcomes (`67`).
- **Metrics** — NDCG@10, precision@5, recall@20, plus a Fitness/Confidence **separation** check (Confidence must correlate with held-out correctness). Run through the shared harness (`62`, `ai/evals/runner.py`) as a **CI gate**, not a docstring.
- **A/B before promote** — embedding/CF/learned weights A/B against the rule-based baseline via `62`; promote only on a measured win; register the winning weights in `model_registry` (`ml_state.py`).

## 8. Build tasks (checklist)

- [ ] Managed embedder registered via `04` (Qwen/Bedrock/Voyage), 1536-d; `ai_matching_v2_enabled` flag (net-new, default off / on-per-env after eval).
- [ ] Program embedder offline job → `embeddings` (entity=`program`), HNSW ANN candidate-gen wired into `match_service`.
- [ ] Student embedder → `student_feature_vectors.embedding`; passed into `score()`; cosine term non-zero in prod.
- [ ] Migration: `program_feature_vectors` table; featurizer populates the sparse vocabulary (eval-gated, source-grounded).
- [ ] CF signal (`implicit`) over the interaction graph; blended at weight 0 cold-start; trained under `67`.
- [ ] Fitness extended (semantic + tag + needs + CF + feasibility), weights in `fitness_breakdown`, fairness-gated (`46` §6).
- [ ] Confidence redefined: real `extractor_quality`, `in_distribution`, calibration hook; no frozen constants.
- [ ] Bands from fitness×feasibility; deterministic + tested.
- [ ] Rated golden set (≥200 pairs) + NDCG@10/p@5/recall@20 + separation check in `62` CI gate.
- [ ] A/B harness vs rule-based baseline; promote-on-win into `model_registry`.
- [ ] Fallback: any model dependency unavailable → rule-based `score()`; never 5xx (`tests/test_plan2_integration.py`).

## 9. Acceptance

- [ ] In a prod-like env, a real student gets matches whose `fitness_breakdown.cosine` is **non-zero** and whose program `soft_align`/`needs` terms reference **populated** program features.
- [ ] Fitness and Confidence move **independently** on a constructed test set (a far-fit program with rich data → low fitness, high confidence).
- [ ] CI fails if NDCG@10 < 0.65 on the golden set; the gate is wired (closes the empty promise at `matching.py:53`).
- [ ] No learned weight or featurizer ships without passing `46` §6 fairness and `62` eval.
- [ ] Disabling `ai_matching_v2_enabled` returns the exact current rule-based scores (clean fallback, tested).
- [ ] `model_registry` records which weights/embedder are live; `ai_turns` records provider/cost for the embed+rerank calls.

## 10. Open questions

- **Embedder choice for v1** — managed (Bedrock/Voyage) now vs Qwen self-host (`63` §8). *Recommend managed → self-host on volume; the win is the wiring, not the host.*
- **Feasibility term source** — `68` admit-history model vs `70` probability bands vs both. *Recommend `70` owns the probability model; `65` consumes it as a feature.*
- **CF cold-start horizon** — interactions needed before `w_cf` > 0 (depends on real traffic). *Recommend gate on count, learned by `67`.*
- **Golden-set authorship** — expert-rated by founder/advisors vs bootstrapped from enrollment outcomes. *Recommend seed expert-rated, grow from outcomes (`67`).*

Sources: internal — `63` §2/§8 (ML boundary, embeddings), `67` (learning loop), `66` (institution side), `68` (data), `62` (eval), `46` §6 (fairness), `56` (shared retrieval); code — `services/matching.py:53,56,72,277,292`, `services/program_features.py:176`, `services/match_service.py:241,289,353`, `api/students.py:965`, `models/matching.py:119`. Papers — `Master Paper.docx`:57,65,67. Benchmark — every incumbent's matching is rule-based (`Competition Analysis`: Common App L916, Niche L1681); evidence-linked dual-score matching is the differentiator.
