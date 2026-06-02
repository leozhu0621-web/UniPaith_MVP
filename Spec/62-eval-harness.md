# 62 · Evaluation Harness — Shared Golden-Set & LLM-Judge Infrastructure

> One evaluation harness, several consumers. The chatbot improvement loop (`61`) and the crawler extraction loop (`60` §13B) both need the *same* machinery: a versioned golden set, an LLM-as-judge calibrated to humans, an offline+CI eval runner, regression gating, A/B comparison, drift detection, and a metrics surface. Build it **once** as a shared internal service any AI surface plugs into.
>
> Status: **draft v1.1** · 2026-05-30 · Resolves the `61` §10 shared-harness question and unifies the golden-set/judge discipline `60` §13B describes. **Builds on the real seed already in the repo:** `ai/evals/runner.py` + `ai/evals/fixtures/` (extend this into the shared harness — don't start fresh) and `ai/agent_registry.py` (the agent→tier map). Reuses `ml_loop` tables (`evaluation_runs`, `training_runs`, `drift_snapshots`, `ab_test_assignments`, `fairness_reports`) + `ai_turns`/`ai_turn_feedback`. Pairs with `45`, `55`, `46`, `60`/`61`/`63`.
>
> **Build anchor:** the harness service = `ai/evals/runner.py` extended with (a) a versioned case store backed by `ai/evals/fixtures/<consumer>/` + `eval_cases`/`eval_results` tables, (b) per-consumer adapters (§5), (c) the calibrated judge (§4), (d) CI gate + A/B + drift modes (§6). Golden sets live as fixtures in-repo; runs persist to `evaluation_runs`.

---

## 1. Why shared

Every AI surface answers the same three questions: *Is it good? Did a change improve it? Is it drifting?* The mechanics are identical; only the cases + rubric differ. Consumers now: chatbots (`61`), crawler extraction (`60` §13B). Future: match rationale (`45` §6), strategy/summary agents, workshop feedback (`14`) — adapter-only. Shared: golden-set store, judge + calibration, runner, CI gate, A/B, drift, metrics. Per-consumer: cases, rubric, a thin adapter (§5). The AI-quality analog of the design system (`02`).

## 2. Core concepts

- **Eval case**: input + expected/rubric + dimensions + metadata (consumer, domain, severity, source=curated|production|synthetic).
- **Golden set**: versioned per consumer; the quality source of truth; **grows from real failures** so nothing re-breaks.
- **Rubric**: per-consumer scored dimensions.
- **Judge**: LLM (or rule) scoring against the rubric, calibrated to humans (§4).
- **Eval run** → `evaluation_runs`. **Gate**: pass/fail (no regression + hard floors).

## 3. Architecture

One service, pluggable consumers, on the `55` substrate. An **adapter** per consumer implements three hooks: `produce(case)→output` (call the agent/extractor), `rubric()` (dimensions + judge prompt), `materialize(production_event)→case` (turn a real failure into a curated case). Everything else (runner, gate, A/B, drift, metrics) is shared.

## 4. LLM-as-judge (the trust foundation)

- **Rubric-driven**: judge scores each dimension 0–1 with a required justification + evidence span (auditable, not vibes).
- **Calibration**: experts hand-label ~200 cases/consumer; iterate the judge prompt to **≥85–90% agreement** before trusting it; record the number; re-calibrate on model/rubric change.
- **Independent judge**: different model family / ensemble than the one under test (avoid self-grading) — for the Qwen extraction, Claude judges; resolves `61`'s open question.
- **Deterministic checks first**: schema validity, PII-leak regex, exact-match, word-count, refusal detection run cheaply; the LLM-judge only handles subjective dimensions.
- **Fairness judge**: a shared dimension flagging protected-class leakage (`46` §6) → writes `fairness_reports`, can hard-gate.

## 5. Per-consumer adapters

| Consumer | produce | rubric | materialize source |
|---|---|---|---|
| Chatbot (`61`) | call agent w/ context | groundedness, constitution, helpfulness, role, safety(hard), voice, tone | 👎 `ai_turn_feedback`, escalations, judge-fails |
| Extraction (`60` §13B) | run extractor on a page | per-field P/R/F1, no-fabrication, schema-validity, normalization | corrections, selector breaks, low-confidence writes |
| Match rationale (future, `45` §6) | generate rationale | factual support, no-fabrication, explainability, no-overpromise | rationale 👎, contested matches |

Adding a consumer = one adapter + a golden set; inherits runner/gate/A-B/drift/metrics.

## 6. Eval modes

1. **CI gate (offline)**: on any prompt/persona/constitution/template/model change, run the affected golden set; **block on regression** of any dimension or any hard-floor failure.
2. **Pre-promote A/B** (`ab_test_assignments`): roll to a cohort, compare scores+feedback+outcomes, promote/rollback.
3. **Production sampling**: continuously sample live outputs, judge, surface rolling per-dimension scores.
4. **Scheduled drift** → `drift_snapshots`: re-run golden sets on a cadence to catch model/provider/knowledge drift; drop alerts.

## 7. Shared synthetic + red-team generation

Synthetic case generation per consumer (chatbot: edge personas/crisis variants; extraction: malformed/foreign pages); red-team battery every release (jailbreaks, essay-coercion, prompt-injection via page content) — any pass blocks; coverage-gap mining clusters traffic for thin areas.

## 8. Data model (reuse + 2 additions)

Reuse `evaluation_runs`, `training_runs`, `ab_test_assignments`, `drift_snapshots`, `fairness_reports`, `ai_turns`, `ai_turn_feedback`. Add **`eval_cases`** (golden set: consumer, domain, input, expected/rubric, dimensions, source, version, severity) + **`eval_results`** (per-case-per-run scores).

## 9. Observability & SLOs

Dashboard per consumer+dimension: rolling production scores, last CI scores, golden-set size/coverage, judge↔expert agreement, A/B deltas, drift, eval cost. SLOs: no golden-set regression shipped; judge agreement ≥85%; zero safety/no-fabrication hard-floor failures in prod; drift below threshold. Alerts on score drop, drift, hard-floor failure (page), agreement decay, cost spike.

## 10. Cost control

Deterministic checks before LLM-judge; cache judge by `(case_hash, output_hash)`; cheapest judge that holds ≥85% agreement; sample rate tuned to budget; full golden set only on change + schedule; track eval tokens (`ai_turns`).

## 11. Phasing

A: primitives (case store + judge + runner + CI gate) with one consumer (chatbot — highest risk). B: add extraction adapter (`60`). C: A/B + drift + production sampling + synthetic/red-team. D: onboard further consumers by adapter. Alongside `60`/`61`.

## 12. Acceptance

- [ ] One service; chatbot (`61`) + extraction (`60`) run through it via adapters — no duplicated eval code.
- [ ] Golden sets versioned, grow from production failures, CI-gated.
- [ ] Judge calibrated ≥85% expert agreement, recorded; deterministic checks first.
- [ ] CI blocks regressions + hard-floor failures (safety/no-fabrication/fairness).
- [ ] A/B before promote; drift on schedule; production sampling live.
- [ ] Red-team every release; any pass blocks.
- [ ] Dashboards + SLOs + alerts; eval cost bounded.

## 13. Open questions

Build vs buy (DeepEval/Confident-AI/Arize for judge+runner; keep golden sets + adapters in-house — recommend). Judge-ensemble cost per dimension. Expert-hours for calibration (shared with `60`/`61`). Outcome-linked eval proxies.

Sources: internal (`45`/`46`/`60`/`61` + `ml_loop`). External: [eval-driven dev](https://www.zenml.io/llmops-database/evaluations-driven-development-for-production-llm-applications) · [LLM-as-judge](https://www.zenml.io/llmops-database/llm-as-a-judge-framework-for-automated-llm-evaluation-at-scale) · [chatbot eval metrics](https://www.confident-ai.com/blog/llm-chatbot-evaluation-explained-top-chatbot-evaluation-metrics-and-testing-techniques) · [eval tools 2026](https://medium.com/online-inference/the-best-llm-evaluation-tools-of-2026-40fd9b654dce).
