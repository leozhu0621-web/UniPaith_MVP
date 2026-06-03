# 67 · Learning Loop & Model Lifecycle — Close the Loop Under Consent

> The papers promise a system that gets smarter: *"permissioned data from both sides continuously sharpening the matching and decision models at its core"* (`Master Paper`:37), trained on *"historical data from partner institutions, with bias avoidance in mind"* (`Master Paper`:65). The substrate is fully built and **fully dormant**: `models/ml_loop.py` defines `outcome_records`, `training_runs`, `evaluation_runs`, `ab_test_assignments`, `drift_snapshots`, `fairness_reports` — and **nothing writes to any of them.** The calibrator (`confidence_calibrator.py:51`) and reranker (`reranker.py`) are permanent identity functions, waiting on 1,000 / 5,000 labeled outcomes that no pipeline produces. `63` §17 explicitly defers this: *"Tuning-data pipeline under `46` consent tiers (own mini-spec)."* This is that spec.
>
> This is the loop that turns `65`'s weights and `66`'s taste model from hand-set to learned, and the **governance** that makes it legal: a per-institution training tier, a hard `consent.training` gate, and a strict separation between customer-specific data and generalized model improvement (`Business Methodology`:822). Without it, `65`/`66` are a one-time guess; with it, they improve every cycle — and only on data the platform is permitted to learn from.
>
> Build anchor: write the dormant `ml_loop` tables; ingest from `enrollment_records` (`35`), `applications` decisions (`34`), yield signals (`35`), and `confidence_outcome_pairs`; reuse the eval harness (`62`, `ai/evals/runner.py`) and `model_registry`/`ml_state.py`. Pairs with `65`/`66` (the models it trains), `46` §9 (consent tiers) + §6 (fairness), `62` (eval-gated promotion), `63` §9 (Qwen tuning), `55` (GPU/queue serving).
>
> Status: **draft v1.0** · 2026-06-02 · activates the dormant ml_loop substrate as a consent-governed, fairness-gated training + promotion pipeline. Closes `47` G-T2/G-T3.

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| `ml_loop` tables (outcomes/training/eval/drift/fairness/AB) | `models/ml_loop.py` (never written) | exists — **write to them** |
| Model registry + routing | `model_registry`, `ml_state.py` | exists — **promotion writes** |
| Calibrator (isotonic) | `confidence_calibrator.py:51` (cold-start) | exists — **feed real pairs** |
| Reranker (learned) | `reranker.py:249` (needs 5k pairs) | exists — **feed real pairs** |
| Outcome ingestion | none | **NEW (build): decision/yield → `outcome_records`** |
| Consent tiers + training gate | `student_data_consent.training` (`46`) | exists — **enforce in pipeline** |
| Eval-gated promotion + A/B | `62` harness | exists — **wire to model promotion** |
| Drift monitoring | `drift_snapshots` (empty) | **NEW (build)** |

## 2. Outcome ingestion — the data the loop runs on

The loop needs **labeled outcomes**, not the `random.uniform` fabrications in `seed_ml_outcomes.py:42`. Ingest real signals as they occur:

- **Decision outcomes** — admit / waitlist / reject and the (student, program) features at decision time, from `applications` (`34`) → `outcome_records` (the label for feasibility + reranker).
- **Yield signals** — offer → enrollment-intent → deposit → enrolled, from `enrollment_records` (`35`) → the label for "qualified-and-converts" (the papers' 50–100 qualified apps/yr target, `Business Methodology`:829).
- **Match-quality feedback** — saves/applies/compares after a match (`28`/`saved_list_items`), and explicit thumbs on rationales (`ai_turn_feedback`) → relevance labels for the reranker + golden-set growth (`65` §7).
- **Confidence outcomes** — predicted-confidence vs realized-correctness pairs → `confidence_outcome_pairs` (the calibrator's training data, §6).
- **Aggregate admit-history corpus** — the typed `program_admissions_history` (`68`) is the standing labeled corpus the feasibility/probability models read (`66`/`70`); §2's per-event ingestion keeps it current, `68` §7's licensed/reported backfill seeds it — never the fabricated rows (`64` §1.6).

Each `outcome_record` carries the consent + tier provenance of its source so §3 can filter at train time. Ingestion is append-only, idempotent (`73` idempotency), and best-effort (never blocks the request path).

## 3. Consent tiers & the training gate — the part that makes it legal

The papers define participation tiers from **"no-training" (use the platform, contribute no training data) to "model partner" (opt-in broad permissioned contribution)** (`Business Methodology`:822), with four governance pillars including *"separation between customer-specific data and generalized model improvements."*

- **Per-institution training tier** on `Institution.data_governance` (`46`): `no_training` (default) | `aggregate_only` | `model_partner`. Only `model_partner` admit history enters the cross-network training set; `aggregate_only` contributes to that institution's own taste model (`66`) but not the shared models.
- **Student `consent.training` is a hard gate** (`46` §9, `student_data_consent.training`). A row with `training=false` **never enters any training set** — enforced at the ingestion filter *and* re-checked at train assembly (defense in depth). This closes `47` G-T2 (no test for `consent.training` enforcement) with an explicit test.
- **Customer/model separation** — customer-specific fine-tunes (a program's own taste model, `66`) are isolated from generalized model improvement (shared embeddings/reranker/CF, `65`); a model-partner's data may improve the shared model, an `aggregate_only`'s may not. Recorded in `training_runs.dataset_provenance`.
- De-identification + minimization before training (`46`); PII-heavy processing stays in-VPC on Qwen (`63` §12).

## 4. Training pipeline

In ROI order (`63` §9), eval-gated throughout (`62`):

- **Classical scoring models** (the `65`/`66` near-term win): CF factors (`implicit`), reranker (`reranker.py` LightGBM/learned), feasibility model, calibrator (§6) — `optuna` HPO (declared, unused), `xgboost`/`sklearn` where they fit. Written to `training_runs` with `algorithm`, `optuna_study_name`, `model_artifact_path`, `fairness_passed`.
- **Qwen LoRA/QLoRA** for the processing models (extraction/normalization/featurization, `63` §9) — separate loop, same gates.
- **Claude agents are NOT trained here** — they improve via the `61` prompt/persona/RAG loop, not by weight updates (`63` §1). Two loops, both on `62`.
- Serving on the `55` GPU/queue fleet (bulkhead; never in the Claude chat path; `63` §10).

## 5. Eval-gated promotion & A/B

No checkpoint reaches users unproven:

1. Train → register in `model_registry` (candidate, not live).
2. **Eval gate** (`62`): no regression on the golden set (`65` §7), no fairness failure (`46` §6), no safety regression. Fail → quarantined, never promoted.
3. **A/B** via `ab_test_assignments`: candidate vs live on a traffic slice; promote only on a measured win (the `65`/`66` acceptance metric).
4. Promote → `ml_state.py` flips the live pointer; the prior version stays rollback-ready.

## 6. Activate the calibrator & reranker

Today both are permanent identity functions because the data never arrives:

- **Calibrator** (`confidence_calibrator.py:51`, MIN 1,000): once §2 produces 1,000+ confidence-outcome pairs, fit isotonic regression; Confidence (`65` §5) stops flowing raw. Until then it flows uncalibrated **and labeled as such** (truthful, `64` §7).
- **Reranker** (`reranker.py:249`, MIN 5,000): once 5,000+ relevance-labeled tuples exist, train `LearnedReranker`; until then `IdentityReranker` (order-preserving, safe).
- Both thresholds are honest floors, not bugs — the fix is *producing the data*, which §2 does.

## 7. Drift & fairness monitoring

- **Drift** — periodic `drift_snapshots` over input feature distributions and score distributions; alert on shift (`57` notifications); a drift trigger schedules a retrain candidate (never an auto-promote).
- **Fairness** — every checkpoint writes a `fairness_reports` row; `46` §6 disparate-impact auto-halt applies to learned scoring exactly as to the rule-based path. Closes `47` G-T3 with a test: a synthetic biased-outcome fixture must trip the halt before promotion.

## 8. Build tasks (checklist)

- [ ] Outcome ingestion: `applications`/`enrollment_records`/feedback → `outcome_records` + `confidence_outcome_pairs`, append-only, idempotent, consent-tagged.
- [ ] Per-institution training tier on `Institution.data_governance` (`no_training`/`aggregate_only`/`model_partner`); default `no_training`.
- [ ] Training-set assembly filter: `consent.training=false` excluded at ingest *and* assembly (double gate); customer/model separation recorded in `training_runs`.
- [ ] Training jobs (classical first: CF/reranker/feasibility/calibrator; `optuna` HPO) → `training_runs` with provenance + `fairness_passed`.
- [ ] Eval-gated promotion (`62`) + A/B (`ab_test_assignments`) + `model_registry`/`ml_state` flip + rollback.
- [ ] Calibrator fit at ≥1,000 pairs; reranker at ≥5,000; both honest-uncalibrated below.
- [ ] `drift_snapshots` job + retrain-on-drift candidate; `fairness_reports` per checkpoint + `46` §6 auto-halt.
- [ ] Tests: `consent.training` exclusion (G-T2); biased-fixture auto-halt (G-T3); promotion blocked on eval/fairness fail.

## 9. Acceptance

- [ ] Real decision + yield outcomes land in `outcome_records`; zero `random.uniform`/hand-coded rows in any prod training path.
- [ ] A student with `consent.training=false` provably contributes to **no** training set (test asserts absence at assembly).
- [ ] A `no_training`-tier institution's admit history never enters the shared model (test); `model_partner`'s may.
- [ ] The calibrator and reranker are **fitted** (not identity) once thresholds are met on real data; Confidence is calibrated.
- [ ] No model promotes without passing `62` eval + `46` §6 fairness; a biased-outcome fixture trips auto-halt before promotion.
- [ ] `training_runs`/`evaluation_runs`/`drift_snapshots`/`fairness_reports` are populated and queryable (the dormant tables are live).

## 10. Open questions

- **Retrain cadence** — per admit cycle vs rolling vs drift-triggered. *Recommend drift-triggered + per-cycle floor.*
- **Aggregate_only contribution** — can differentially-private aggregates from non-partner tiers improve shared models safely? *Recommend defer; partner-tier only for v1.*
- **Outcome-label latency** — enrollment outcomes lag matching by months; how to learn before labels mature. *Recommend proxy labels (apply/save) early, replace with true outcomes as they arrive.*
- **Serving host** — Bedrock-managed training/serving vs self-host GPU (`63` §17, `55`). *Recommend managed first.*

Sources: internal — `65`/`66` (models trained), `46` §6/§9 (fairness + consent tiers), `62` (eval-gated promotion), `63` §9/§10 (Qwen tuning/serving), `35` (yield), `34` (decisions), `55` (serving); code — `models/ml_loop.py`, `services/confidence_calibrator.py:51`, `services/reranker.py:249`, `services/ml_state.py`, `scripts/seed_ml_outcomes.py:42`. Papers — `Master Paper.docx`:37,65; `Business Methodology.docx`:820,822,829.
