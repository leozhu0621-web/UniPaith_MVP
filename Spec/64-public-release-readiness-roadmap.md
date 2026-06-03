# 64 · Public-Release Readiness — Backend Master Roadmap

> The MVP is **feature-complete on the surface and hollow at the core.** Every screen the papers describe exists; the engine the papers describe does not. The matching engine — the literal "secret sauce" of the Business Methodology — is a hand-tuned heuristic whose dominant signal is **dead in production**: the embedding term (0.45 of fitness) never fires because the live path passes no vectors (`match_service.py:289`, `api/students.py:983`), and the program side reads a `Program.feature_vector_sparse` column **that was never created** (`program_features.py:176`). The "ML core" of `63` is a **docs-only architecture decision** — no Qwen, no training, no serving; `models/ml_loop.py` (`training_runs`/`outcome_records`/`drift_snapshots`) is **scaffolding nothing writes to.** "Historical partner data" is **~14 fabricated rows** (`seed_dev_data.py:475`); program outcomes are an **untyped JSONB blob** (`institution.py:211`); the catalog is **9 hand-coded CS programs** (`seed_dev_data.py:382`). That is the gap between *prototype* and *product*.
>
> This spec is the **index and sequencing** for closing it. It does not introduce schema or build tasks of its own — it frames the problem, inventories what is genuinely real (so the detail specs *operationalize* the large dormant substrate rather than rebuild it), and sequences **`65`–`74`** into four release blocks mapped to the founder's four prototype-vs-product axes: **matching rigor, data realism, product completeness, production hardening.** Each detail spec aligns to the founding papers (`Master Paper` / `Business Methodology`) and to the four benchmark categories named for this work — discovery/match (Niche, Studyportals, Appily, BigFuture), application platforms (Common App, Liaison, ApplyBoard), two-sided/networking (LinkedIn, Handshake, Unibuddy), and rec/onboarding (Coursera, Duolingo, Hinge).
>
> Companion architecture already specced (these are the *plans*; `65`–`74` are the *execution* + net-new): `06` (3-layer engine), `55` (production readiness), `56` (search/feed/recs), `57` (realtime), `58` (security), `60` (crawler), `62` (eval harness), `63` (ML boundary), `46` (consent/fairness), `45` (agent inventory).
>
> Status: **draft v1.0** · 2026-06-02 · first public-release readiness roadmap. Grounds the prototype→product gap in a code audit and sequences `65`–`74`. Supersedes nothing; indexes the new backend block.

---

## 1. The prototype gap (the honest finding)

A code-level audit against the papers found the product is **a real presentation layer wrapped around a stubbed brain.** Ranked by how much each undermines the "AI matching platform" claim:

1. **The match score is a dead heuristic.** Live fitness collapses to `0.35·soft_align + 0.20·needs_match` because the 0.45 cosine term gets no embeddings (`matching.py:277` → always `0.0`), and *both* soft-side and needs-side program features are empty — `program_features.py:176` reads `Program.feature_vector_sparse`, a column absent from every model and migration. Net: **rule filter + student-only tag overlap against empty program tags.** Most surviving programs get near-identical low fitness.
2. **No ML anywhere.** No collaborative filtering, no learned weights, no training. Weights are three hand-tuned constants (`matching.py:56`). `implicit`/`xgboost`/`optuna`/`shap`/`hdbscan` are declared in `pyproject.toml` and **imported nowhere in `src/`.** The `embeddings` pgvector HNSW table (`models/matching.py:119`) is fully built and **never written** — a monument to intended-but-absent semantic matching.
3. **`63`'s ML core is unbuilt.** Docs-only. No Qwen, no vLLM, no model serving, no `.fit()`/`.predict()` on real data. `IdentityReranker` (`reranker.py:84`) and identity calibrator (`confidence_calibrator.py:163`) are the prod paths, permanently cold-start (need 5,000 / 1,000 labeled outcomes that don't exist).
4. **Confidence is static.** Two of its four geometric-mean factors are frozen constants — `extractor_quality=0.85` (`matching.py:72`), `extrapolation=1.0` (`matching.py:292`). The dual Fitness+Confidence story exists in schema and UI but Confidence carries little real signal.
5. **Outcomes data has no schema.** `Program.outcomes_data`/`cost_data` are untyped JSONB (`institution.py:211,216`). The salary distributions / employment rates / employer concentration / payback bands / placement geography the papers promise (`Business Methodology` §Outcomes) have nowhere typed to live, so Featured filters/sorts and the Outcomes detail section have nothing real to bind to.
6. **"Historical partner data" is fabricated.** `HistoricalOutcome` = ~14 hardcoded round-number rows (`seed_dev_data.py:475`); `seed_ml_outcomes.py:42` generates 120 more with `random.uniform`. There is no real outcome corpus to train, calibrate, or measure against.
7. **The catalog is a demo.** 3 institutions / 9 programs, all hand-coded, all CS/DS-flavored (`seed_dev_data.py:261,382`). No ingestion populates it at volume.
8. **No institution "taste" model.** `InstitutionFeature` (`models/matching.py:103`) is a stub table nothing writes. The papers' core institution-side mechanism — reverse-projecting admit history into student-profile vocabulary (`Master Paper`:76) — does not exist.
9. **Production infra is modest and per-replica.** Health/`/ready`/JSON-logging/PII/realtime are real (`55`/`57`/`58` partially landed), but cache is in-process only (`core/cache.py:130` `backend="memory"`; `redis` isn't even a dependency), rate-limit is in-memory IP-keyed (won't coordinate across ECS tasks), there are no metrics/tracing, and no distributed queue. `55` *describes* the fixes; they are **not built.**
10. **No match-quality measurement.** The `matching.py:53` "exit gate: NDCG@10 ≥ 0.65 against 100 internally-rated pairs" has **no rated set and no eval.** 122 test files validate formulas and wiring; none validate that matches are *good*.

**One thing is genuinely real and must be protected:** the LLM *presentation* layer — `ai/rationale.py` (groundedness-checked, cached, consent-gated), discovery extractor/validator, workshops, strategy, identity — are real Claude calls with provider failover and rule-based fallbacks, enabled in prod. Per `63`'s seam, **Claude communicates; the thing that's supposed to compute underneath does not yet.** Every detail spec preserves the "never 5xx → rule-based fallback" invariant (`tests/test_plan2_integration.py`).

## 2. What's already real (operationalize, do not rebuild)

The schema substrate is enormous (**107 tables**, `51`) and mostly dormant. The detail specs wire it; they must not re-propose it.

| Already built | Where | The new spec that activates it |
|---|---|---|
| `embeddings`, `student_feature_vectors` (`Vector(1536)`), `model_registry`, `prediction_logs`, `confidence_outcome_pairs`, `ml_state` | `models/matching.py`, `services/ml_state.py` | `65`, `67` |
| `ml_loop`: `outcome_records`, `training_runs`, `evaluation_runs`, `drift_snapshots`, `ab_test_assignments`, `fairness_reports` | `models/ml_loop.py` (never written) | `67` |
| `InstitutionFeature` stub | `models/matching.py:103` | `66` |
| `confidence_calibrator.py`, `reranker.py` (interfaces, cold-start) | `services/` | `65`, `67` |
| Structured reviews: `StudentProgramReview` (7 dims), `EmployerFeedback` (6 dims) | `institution.py:1017,1063` | `68` |
| Crawler/knowledge engine + `scholarships` + reference graph | `services/crawler/`, `60` | `69`, `70` |
| LLM presentation agents (rationale, discovery, strategy, workshops) | `ai/` | preserved by all; scored by `62` |
| Follow graph + peer/ambassador scaffold (`institution_follows`, `peer_profiles`) | `models/follow.py`, `models/peer.py` (`20`) | `71` (adds live chat, ambassadors, RAG agent) |
| Health/`/ready`, JSON logging, PII registry, CSP, SSE/WS realtime | `core/`, `55`/`57`/`58` | `73` (finish the rest) |
| Shipped feature verticals: international `38`, fees `39`, recruitment `40`, graduate `41`, decisions/offers `34`, audit `36`, fairness/consent `46` | live | extended by `70`/`72`/`74`, not redone |

## 3. The release blocks (the index)

Each detail spec opens with its own `What exists vs what to build` table and follows house style (`55`/`62`/`63`). Tags: **[paper]** = papers obligation, **[bench]** = benchmark-driven, **[focus]** = founder's four axes.

### R1 — Make the core real · *matching rigor*
- **`65` · Matching Engine, For Real.** Wire embeddings into the live path (kill the dead cosine); build the missing **program-side feature vectors** (the phantom column); define **Fitness** (predicted fit/admit-and-outcome) vs **Confidence** (data-sufficiency × model-certainty) as real, separable formulas; hybrid pgvector-semantic + structured + collaborative-filtering scoring; bands (best-fit/stretch/safer); a **match-quality eval** (NDCG@10 / precision@k on a rated golden set). *[paper §1: "CF + pattern recognition + feature vectors"]* *[bench: every incumbent's matching is rule-based — this is the differentiator UniPaith is named for]* *[focus: matching rigor]*
- **`66` · Institution Taste & Ideal-Student Model.** Reverse-project partner admit-history into the student-profile feature space; populate `InstitutionFeature`; virtual-student generation + conversational faculty tuning; bias-avoidance constraints; segmentation bands (fit / likelihood-to-apply / nurture-needed). *[paper §2: "turn the school's 'taste' into UniPaith's language"]* *[focus: matching rigor]*
- **`67` · Learning Loop & Model Lifecycle.** The consent-tiered tuning-data pipeline (`63` flagged "own mini-spec"): ingest decision-outcomes + yield signals into the dormant `ml_loop` tables; per-institution training tier (no-training ↔ model-partner) + `consent.training` hard gate + customer-data / model-improvement separation; eval-gated promotion (reuse `62`); activate the calibrator + reranker. *[paper §5: "permissioned data continuously sharpening the models"]* *[focus: matching rigor]*

### R2 — Make the data real · *data realism & depth*
- **`68` · Outcomes & Admissions-History Data Layer.** Typed schema replacing the JSONB blobs: salary distributions, employment/underemployment, employer concentration, hire rate, internship-to-offer, payback bands, placement geography; admit rates / yield / class profiles / trends (replace the fabricated `HistoricalOutcome`); school-vs-program separation. Feeds `65`/`67`/`70` and Featured filters. *[paper §3]* *[bench #2: the table-stakes that separate "finished" from "demo"]* *[focus: data realism]*
- **`69` · Program Catalog Ingestion at Scale.** From 9 hand-coded programs to a real ingestion pipeline — institution-direct upload (column-mapping, ID normalization, validation, usage-scope consent), crawl (extend `60`), editorial; dedupe, CIP/SOC normalization, freshness/TTL, provenance + first-party-wins; SEO-indexable records. *[bench #1: the single biggest prototype-vs-product gap — Studyportals 240K programs, Niche]* *[focus: data realism]*
- **`70` · Financial Fit & Direct Admission.** Scholarship catalog (eligibility + award value, extend `60`) + Scholarship-Finder; Net-Price/EFC estimator; **reverse-admissions / direct-admit engine** — institution eligibility rules → proactive guaranteed-admit + scholarship offers to matching profiles; admit-probability bands. *[paper: Persuasion / custom aid package]* *[bench #3/#4: Niche Direct Admissions 1M+ offers, Common App DA, Appily $6B]* *[focus: data realism + completeness]*

### R3 — Make it two-sided & trustworthy · *product completeness*
- **`71` · Connection Graph & Social Activation.** The follow graph + Peers tab are **already shipped** (`models/follow.py` `InstitutionFollow`, `models/peer.py`; the "`student_follows` unbuilt" note at `51`:148 is stale, corrected in `71` §2) — `71` adds the *live* layers genuinely missing: peer↔ambassador tag-matching, live chat over `57` (peers are async-Inbox-only today), community spaces + ambassador-hosted events, and an institution-facing conversational RAG agent bounded to institution content with confidence-gated human handoff + chat→CRM summary. *[paper: Stage 3a "semi-social Handshake model"]* *[bench: LinkedIn/Handshake/Unibuddy — "integrate, don't rebuild"]* *[focus: completeness]*
- **`72` · Verification & Integrity Intelligence.** Transcript parsing/OCR + GPA-normalization + prerequisite checker; tamper-evident document/credential verification (hash-based; WES/ECE; ETS/British Council score verify); fraud / anomaly / duplicate-identity / trust scoring; **third-party-applicant auto-profiling** (build a profile from raw materials, `Master Paper`:90); 24–48h verification SLO; human-approval fallback (human-in-loop invariant). *[paper: Review/authenticate]* *[bench #8/#9: ApplyProof, Liaison coursework verification]* *[focus: completeness]*

### R4 — Make it survive launch · *production hardening*
- **`73` · Launch Hardening & Scale.** Execute the still-unbuilt `55` items the audit found: wire Redis/ElastiCache cache, distributed rate-limit, arq queue, `core/idempotency.py`, circuit breakers, metrics + OTel tracing, the index migration (FK / JSONB GIN / pgvector ANN); **deadline-surge scalability** (Common App's known Nov-1 outage mode); universal application fan-out (apply-once→submit-to-many) at scale. *[bench: surge-fragility is a winnable incumbent weakness]* *[focus: production hardening]*
- **`74` · Interoperability, i18n & Compliance-Ops.** CRM import/export — Slate (SFTP/XML + REST), Salesforce, Common App/Coalition import, webhooks (**wrap-around-Slate, not rip-replace** — the doc's hard constraint); multilingual/i18n advisor; SOC 2 Type II / FERPA / GDPR / CCPA compliance-ops + per-institution data residency. *[bench #7: Slate is the highest switching cost; College Board's NY-AG settlement is the consent template to pre-empt]* *[focus: completeness + procurement-readiness]*

## 4. Sequencing & dependencies

Build order is **data → engine → activation → hardening**, because a learned engine on fabricated data is worse than an honest heuristic.

```
68 (outcomes/admit schema) ─┬─► 65 (matching real) ─► 66 (institution taste) ─► 67 (learning loop)
69 (catalog ingestion) ─────┘            │                                          ▲
70 (financial/direct-admit) ◄────────────┘                                          │
                                                                                    │
67 ──(needs real outcomes from)──► 68 + 70 (yield/decision signals) ────────────────┘

71 (connection)  72 (verification)  — independent; can run parallel to R1/R2
73 (hardening)   74 (interop/i18n/compliance) — continuous; 73 gates the public-launch load test
```

- **`68` and `69` are the critical path.** `65`'s embeddings need real program text/outcomes; `67`'s training needs real outcomes; `70`'s net-price needs real cost data. Ship the typed schema + ingestion first, even before the engine.
- **`65` before `66` before `67`.** Fix the student-side score, then learn the institution side, then close the loop. Each is fairness-gated (`46` §6) before any real cohort.
- **`73`/`74` run continuously** but `73`'s surge/load test is the **hard gate** on flipping public signup on.
- **Nothing in R1 ships to users on fabricated data.** Until `68`/`69` land real data, the rule-based path stays the default per-environment flag (the existing fallback invariant); the learned path A/Bs behind `62` and promotes on a measured win.

## 5. Alignment map — papers ↔ specs

| Founding-paper claim | Source | Spec |
|---|---|---|
| "LLM → feature vectors → ML engine (CF + pattern recognition) → LLM reasoning" | `Master Paper`:67 | `65` (ML), `63` (boundary) |
| Fitness Level + Confidence Level (named, undefined) | `Master Paper`:57 | `65` (defines both) |
| Train on historical partner data, bias avoidance | `Master Paper`:65 | `67`, `66`, `46` §6 |
| Institution "taste" → ideal-student in student-profile language; virtual student | `Master Paper`:76,78 | `66` |
| "Continuously sharpening models from permissioned data" | `Master Paper`:37 | `67` |
| Outcomes (salary/employment/employer/payback/placement) | `Business Methodology`:121-128 | `68` |
| Two-graph reviews (student dims + employer dims) | `Business Methodology`:184-194 | `68` (schema exists; aggregation) |
| Semi-social "Handshake model" connection & outreach | `Master Paper`:61 | `71` |
| Workshops feedback-only ("Not generating context") | `Master Paper`:61 | preserved (CI contract, `14`) |
| Authenticate materials / third-party auto-profiling / fraud rule-out | `Master Paper`:90 | `72` |
| Human-in-the-loop for all decisions | `Master Paper`:88 | invariant in `66`/`70`/`72` |
| 99% uptime · 24–48h verification · 50–100 qualified apps/yr/institution | `Business Methodology`:829 | `73` (uptime), `72` (verify SLO), `70`/`67` (qualified routing) |

## 6. Release gate (acceptance)

The product is **publicly releasable** when:

- [ ] **The match score means something.** Embeddings flow end-to-end (cosine term non-zero in prod); program-side feature vectors exist and are populated; a held-out **NDCG@10 ≥ 0.65 / precision@5** on a ≥200-pair rated golden set, measured in CI (`65`, `62`). No surface ships scores computed on empty features.
- [ ] **Fitness and Confidence are independently real.** Both formulas defined and tested; Confidence reflects actual data-sufficiency × model-certainty, no frozen constants (`65`).
- [ ] **Data is real, not seeded.** Program catalog populated by ingestion at realistic scale with provenance + freshness (`69`); outcomes/admit data typed and populated where available (`68`); zero `random.uniform`/hand-coded rows in any prod path.
- [ ] **The learning loop is closed and governed.** Decision/yield outcomes ingest into `ml_loop`; `consent.training=false` data never trains (test-enforced, closes `47` G-T2); every checkpoint fairness-gated (`46` §6, closes G-T3); model promotion is eval-gated (`67`/`62`).
- [ ] **Institution side learns.** `InstitutionFeature` populated from admit history; virtual-student + tuning live; bias-avoidance verified (`66`).
- [ ] **It survives launch.** Distributed cache + rate-limit + queue + idempotency + circuit breakers + metrics live; load test sustains a deadline-surge profile at p95 within SLO and 99% uptime (`73`).
- [ ] **It interoperates and complies.** Slate/Common App import-export proven against fixtures; FERPA/GDPR/CCPA review passed; SOC 2 Type II readiness documented (`74`, closes `47` G-C1).
- [ ] **The invariant holds.** Every AI surface still falls back to rule-based on failure; no 5xx from a model path (`tests/test_plan2_integration.py`).

## 7. Open questions

- **Embeddings provider for the first real move** — Qwen3-Embedding self-host vs Bedrock vs Voyage (`63` §8 recommends Matryoshka→1536, no migration). Start managed; the first measurable win is `65`'s, not `63`'s abstract migration. *Recommend: managed embeddings now, defer self-host to volume.*
- **Where does real data come from?** `68`/`69` must decide sourcing per field — institution-reported (partner DPAs), crawled (`60`, public-non-personal only), or licensed (IPEDS/College Scorecard for U.S. outcomes). *Recommend: IPEDS/Scorecard seed for U.S. outcomes + partner-reported overlay; first-party-wins.*
- **Heuristic honesty in the interim.** Until learned models beat the heuristic on `62`, do we show Confidence that openly reflects thin data (lower scores) rather than the current static 0.85? *Recommend: yes — truthful low confidence beats false precision.*
- **Scope of R3/R4 for v1 public release vs fast-follow** — `71` ambassador chat and `74` full CRM interop may be fast-follow if the launch is student-discovery-first. Sequenced here; gated by GTM.

Sources: internal — `06` (engine), `45` (agents), `46` (consent/fairness), `51` (data model), `55` (production), `60` (crawler), `62` (eval), `63` (ML boundary); code — `services/matching.py`, `services/program_features.py`, `services/ml_state.py`, `models/ml_loop.py`, `models/matching.py`, `scripts/seed_dev_data.py`. Papers — `Master Paper.docx`, `Business Methodology.docx`. Benchmarks — `Competition Analysis.docx` (Niche, Studyportals, Common App, Liaison, ApplyBoard, Unibuddy, EAB, Mainstay).
