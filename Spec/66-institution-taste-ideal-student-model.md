# 66 · Institution Taste & Ideal-Student Model — Reverse-Project Admit History

> The papers call this the differentiator: *"the secret sauce of matching candidates to the right institutions … is understanding the institution's 'tastings' on the three factors: basic background, personality & behavior preferences, and self-identity"* (`Master Paper`:65). The mechanism is explicit — *"let our system understand the 'ideal student type' … turn the school's data pattern, or 'taste', into UniPaith's language, which is the characteristic in the student's profile … through data dumping … our ML model would recognize the pattern and present in the language of our student profile points"* (`Master Paper`:76), plus a **virtual student** faculty tune conversationally each cycle (`Master Paper`:78).
>
> None of it exists. `InstitutionFeature` (`models/matching.py:103`) is a stub table (`feature_data JSONB`) nothing writes. There is no reverse-matching, no learned institution preference vector, no virtual student. Matching is one-directional (student→program) and the program side of the score is empty (`65` §3). This spec builds the **institution-side model**: project each program's admit history into the *same* feature vocabulary as the student profile (`42`), so a program's "ideal student" is a vector comparable to any real student — the feature that makes Fitness (`65` §4) bidirectional and feasibility (`65`/`70`) real.
>
> Build anchor: populate `InstitutionFeature`; consume the admissions-history upload (`69` §institution-direct) and `HistoricalOutcome` (`models/application.py`); same taxonomy as `42`. Pairs with `65` (consumes the taste vector), `67` (learns + retrains it), `70` (reverse-admissions uses it), `46` §6 (bias-avoidance is mandatory here), `63` §2 (Qwen pattern-recognition).
>
> Status: **draft v1.0** · 2026-06-02 · builds the institution "taste"/ideal-student model the papers center on; never ships a checkpoint that fails fairness.

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Institution feature table | `InstitutionFeature` stub (`matching.py:103`) | exists — **populate** |
| Admissions-history store | `HistoricalOutcome` (~14 fabricated rows) | exists — fed real by `69`/`67` |
| Admit-history → ideal-student vector | none | **NEW (build): reverse-projection model** |
| Virtual student (synthetic exemplar) | none | **NEW (build): generate from taste vector)** |
| Conversational cycle tuning | none | **NEW (build): faculty LLM tuning surface** |
| Segmentation bands (fit/likelihood/nurture) | none | **NEW (build)** |
| Bias-avoidance on the taste model | `46` §6 fairness (student side) | exists — **extend to taste model** |

## 2. Data dumping — admit history in, comparable signals out

The institution-direct upload (column-mapping templates, program-ID normalization, validation, **usage-scope consent** marketing-only / admissions-ops / analytics / training) is the generic ingestion built in `69`; `66` is its first heavy consumer. From the consented admit history per program — applicant attributes + decisions + yield — derive a clean, de-identified training table keyed to programs. **`consent.training=false` and non–model-partner-tier institutions never enter the training set** (`46` §9, `67` §3). The papers' "data dumping" (`Master Paper`:76) is exactly this: raw history → normalized signals in the student-profile vocabulary (`42`).

## 3. The taste model — reverse projection into student-profile space

For each program, learn an **ideal-student representation in the same feature space as a real student** (the `42` signal vocabulary + the `Vector(1536)` embedding):

- **Pattern recognition (Qwen / classical, `63` §2.4).** Over the program's admitted-and-enrolled cohort, learn the central tendency + spread of each feature axis (interest themes, career arcs, values, support needs, academic band) and a centroid embedding. Store as `InstitutionFeature.feature_data` (the sparse "ideal" vocabulary that `matching.py` already reads on the program side, `65` §3) + an ideal-student `embedding`.
- **Three factors (`Master Paper`:65).** The taste vector spans the same three layers as the student profile — basic background / personality & behavior / self-identity — so student↔ideal comparison is apples-to-apples on every axis.
- **Admit-feasibility signal.** The model also yields, per (student, program), a learned **feasibility** = how close this student sits to the program's admit distribution — the `65` §4 `admit_feasibility` term and the input to `70` probability bands. Distinct from demographic similarity (see §5).
- **Cold-start.** A program with thin history falls back to its stated requirements + editorial profile (`68`/`69`); `data_completeness` reflects this and dampens Confidence (`65` §5). Never fabricate a taste vector from no data.

## 4. Virtual student & conversational tuning

- **Virtual student (`Master Paper`:78).** Generate a synthetic exemplar profile from the program's taste vector — a readable "this is who thrives here" student, **never a real or re-identifiable applicant** (`46`, k-anonymity floor on the generating cohort). Powers the program's "who thrives / who should avoid" panel (`Business Methodology`:186) and gives faculty something concrete to react to.
- **Tuning (`Master Paper`:78).** Faculty steer **this cycle's** targeting by conversing with an LLM against the virtual student — "we want more first-gen research-curious applicants this year" → adjust the *cycle weighting* over the taste axes, **without retraining the base model**. The tuning is a per-cycle overlay (versioned, `student_strategies`-style clone-and-modify), auditable (`36`), and **bounded by fairness** (§5) — faculty cannot tune toward a protected attribute. The conversation is Claude (human-facing, `63` §3); the taste model underneath is Qwen/classical.

## 5. Bias-avoidance — non-negotiable

The papers state it three times (`Master Paper`:65,76,88). The taste model is the **highest bias risk in the platform** — it learns from historical admit decisions, which encode historical bias.

- Protected attributes (and known proxies) are **excluded from the taste vector and the feasibility term** (`46` §6 registry); a proxy-detection pass flags any feature whose signal correlates with a protected class above threshold.
- Every taste-model checkpoint and every cycle-tuning overlay passes **`46` §6 disparate-impact** before it touches a real cohort; failure → auto-halt (`programs.matching_halted`) and surfaces on the fairness dashboard. This closes `47` G-T3 (no test for disparate-impact auto-halt) on the institution side.
- The model learns *what kind of student thrives*, not *who got admitted before* — the training target is **enrolled-and-succeeded** signals where available (`68` outcomes), not raw admit decisions, to break the historical-bias loop.

## 6. Segmentation bands

For institution dashboards and `70` activation, the taste model emits per-prospect bands (`Business Methodology`:577-580): **fit-to-program-family** (high/med/low), **likelihood-to-apply**, **nurture-needed** (high interest, low readiness). Aggregate-on-read over the existing prospect/recruitment data (`40`); feeds Pinpoint targeting and reverse-admissions eligibility (`70`).

## 7. How it feeds the rest

- `65` §4 reads the program taste vector for `soft_align`/`needs` (no longer empty) and the `admit_feasibility` term.
- `70` reverse-admissions uses fit + feasibility bands to decide which students get a proactive direct-admit/scholarship offer.
- `67` retrains the taste model as new cycles close; drift-monitored (`drift_snapshots`).

## 8. Build tasks (checklist)

- [ ] De-identified per-program training table from consented admit history (`69` upload; `46` §9 gate; non-model-partner tier excluded).
- [ ] Taste model → `InstitutionFeature.feature_data` (sparse ideal vocabulary) + ideal-student `embedding`; same taxonomy as `42`.
- [ ] `admit_feasibility(student, program)` exposed to `65`/`70`.
- [ ] Virtual-student generator (k-anonymity floor; never re-identifiable); powers "who thrives" panel.
- [ ] Conversational cycle-tuning surface (Claude) → versioned per-cycle weighting overlay; audited (`36`); fairness-bounded.
- [ ] Segmentation bands (fit/likelihood/nurture) aggregate-on-read for `40`/`70`.
- [ ] Proxy-detection + `46` §6 gate on every checkpoint and overlay; auto-halt on failure.
- [ ] Flag `ai_institution_taste_v2_enabled`; rule-based stated-requirements fallback when off or cold-start.

## 9. Acceptance

- [ ] A program with real admit history shows a populated `InstitutionFeature` ideal-student vector in the `42` vocabulary; a thin-history program honestly shows low completeness and falls back to stated requirements.
- [ ] `65`'s program-side `soft_align`/`needs` terms read this vector (no longer empty).
- [ ] A virtual student renders for a program and is verifiably non-re-identifiable (k-anonymity test).
- [ ] Faculty cycle-tuning adjusts targeting and is **blocked** when it would tune toward a protected/proxy attribute (test).
- [ ] No taste checkpoint or overlay ships without passing `46` §6; a synthetic biased-history fixture triggers auto-halt.

## 10. Open questions

- **Model class for pattern recognition** — Qwen embedding centroid + classical density vs a learned classifier (`63` §2). *Recommend embedding-centroid + per-axis distribution first; classifier when data justifies.*
- **Training target** — enrolled-and-succeeded vs admitted (bias). *Recommend succeeded-where-available, admitted as fallback, documented.*
- **Min cohort for a taste vector** — the k-anonymity + statistical floor. *Recommend ≥ a fixed k; below it, requirements-only.*
- **Cycle-overlay persistence** — does this year's tuning decay automatically next cycle? *Recommend yes, explicit re-confirm.*

Sources: internal — `65` §3/§4 (consumes taste), `67` (retrains), `70` (activates), `46` §6/§9 (fairness + consent), `63` §2 (Qwen), `40` (prospects), `42` (signal vocabulary), `36` (audit); code — `models/matching.py:103` (`InstitutionFeature`), `models/application.py` (`HistoricalOutcome`). Papers — `Master Paper.docx`:65,76,78,88; `Business Methodology.docx`:498-511,577-580.
