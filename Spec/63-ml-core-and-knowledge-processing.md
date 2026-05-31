# 63 · ML Core & Knowledge Processing — Qwen (ML backend) + Claude (agent)

> The platform runs on **two models with a hard, non-negotiable boundary**:
> - **Qwen** (open-source, self-hosted, self-tuned) = the **ML backend**. It processes information and synthesizes the info that's *presented* on the frontend. **It never interacts with a human directly** — the invisible brain, not the voice.
> - **Claude** (API) = the **conversational agent + all human-facing advisory reasoning** — the advisor chatbot (`61`) and the reasoning agents (`45`) that speak to a specific person. This stays Claude.
>
> Also specifies how raw crawled info (`60`) becomes structured, embedded, scored, **presented** knowledge — Qwen's job.
>
> Status: **draft v2.0** · 2026-05-30 · v2.0 replaces an earlier "hybrid decided per-task by eval" framing with the founder's **hard rule: Qwen = ML backend (no human interaction); Claude = the chatbot/agent.** Pairs with `06`, `60`, `61`/`62`, `46`, `55`, `45`, `04`.

---

## 1. The boundary (the rule everything follows)

*Qwen is the ML/data brain; Claude is the mouth.* If an output is a **conversation with, or personalized advice to, a human → Claude.** If it is **data processing, scoring, or synthesis of informational/display content → Qwen.** No exceptions, no per-task drift.

| | Qwen — ML backend (invisible) | Claude — the agent (human-facing) |
|---|---|---|
| Role | processes, scores, ranks, embeds, **synthesizes displayed info** | **talks to people**; personalized advice |
| Human interaction | **none** — batch/inline services | **direct** — chat, advisory prose |
| Why | open, self-hosted, tuned, cheap at volume, PII in-VPC | premium reasoning, brand voice (`01` §6), trust, safety (`61`) |
| Where | GPU/Bedrock worker fleet (`55`) | Anthropic API / Bedrock via `04` |

Why a *hard* rule, not eval-decided: the conversation is the brand + trust surface. It stays Claude as a **product decision**, independent of whether tuned Qwen could match it. (Supersedes v1's "Phase-D Qwen-takes-advisor" path — removed.) Reconciles with "agents trained on Claude" (`04`/`45`): the agents stay Claude; Qwen is added *underneath* as the ML backend.

## 2. What Qwen does (no human contact)

Non-conversational services / batch jobs; outputs are data/scores/vectors or synthesized *informational* content:
1. **Embeddings** — programs, schools, scholarships, knowledge docs, student feature-vectors → pgvector. Powers matching, search (`56`), dedup (`60`). (§8.)
2. **Crawler extraction** (`60` §13) — page → structured fields, eval-gated (`62`).
3. **Normalization / classification / entity-resolution** (`44`, `60`) + change-materiality (`60` §3B).
4. **L3 ML scoring + ranking** (`06`) — fitness/confidence, CF, re-rank, risk/anomaly scores.
5. **Knowledge synthesis for display** — scattered facts → the factual content on a program/school page (outcomes summary, career panel, net-price, "typical for this field"). Presenting, not conversing; brand-voice + groundedness eval-gated (`62`); source-cited.
6. **Search + feed ranking** (`56`).

Processing `45` agents are Qwen-served: DiscoveryExtractor, DiscoveryValidator, DiscoveryQueryInterpreter, DocumentParseTriage, AuthenticityRiskScorer, SegmentBuilderNLBridge.

## 3. What Claude does (human-facing, stays Claude)

- **Advisor chatbot** (`61`/`19`) — always Claude.
- **Match rationale / "why this match"** (`45` §6) — the *score* is Qwen's; the *explanation* is Claude's.
- **Essay/interview/test feedback** (`14`, `45` §7–9).
- **Strategy narrative, identity summary** (`45` §10–11).
- **Faculty review summaries, inbox drafts, campaign copy** (`45` §13–16).
- **Eval judge** (`62`).

Seam rule: **Qwen computes; Claude communicates.** A match card = Qwen numbers + Claude rationale. A program page = Qwen-synthesized facts; ask the chatbot about it → Claude (grounded by Qwen's RAG).

## 4. Model roster

| Task | Model | Provider |
|---|---|---|
| Embeddings | Qwen3-Embedding (8B/4B/0.6B; Matryoshka→1536) | Qwen self-host/Bedrock |
| Reranking | Qwen3-Reranker | Qwen |
| Crawler extraction (`60`) | Qwen3-Instruct 14–32B, tuned | Qwen |
| Normalization/classification/triage/scoring | Qwen3-Instruct 7–14B | Qwen |
| L3 fitness/confidence/CF/rank | Qwen embeddings + classical ML (`matching.py`) | Qwen + in-process |
| Display synthesis (factual) | Qwen3-Instruct, brand-voice eval-gated | Qwen |
| **Advisor chatbot** (`61`) | **Claude** Sonnet/Haiku | Anthropic/Bedrock |
| **Rationale/feedback/strategy/summaries** (`45`) | **Claude** Sonnet/Opus | Anthropic/Bedrock |
| Eval judge (`62`) | Claude/ensemble | Anthropic/Bedrock |

Routing in `model_registry` + `04`; Qwen is a registered transport. **Human-facing rows pinned to Claude by policy** — not eligible for reassignment.

## 5. Knowledge-processing pipeline (raw → presented) — Qwen

`(60)` raw doc → EXTRACT (Qwen, schema-strict, grounded `62`) → NORMALIZE (units/SOC/CIP/CEFR/currency/grading) → RESOLVE (link → entities) → EMBED (Qwen3-Embedding 1536d → pgvector) → ENRICH-WRITE (confidence-gated, provenance, first-party-wins `60`) → SYNTHESIZE (Qwen → presented facts, sourced, brand-voice `62`) → SERVE (frontend + RAG index for the Claude advisor + feature vectors for L3). Two speeds (`60` §6): official API/bulk skips extract; crawl runs full path.

## 6. The 3-layer engine (`06`) realized

- **L1 collect**: student inputs (`42`) + crawler world-knowledge (`60`). No model.
- **L2**: **Qwen** invisible conversion (extract → signals + embeddings → vectors, + display synthesis); **Claude** human-facing reasoning (chat, rationale, feedback).
- **L3 ML core**: Qwen embeddings → pgvector ANN + classical calibrated scoring (`model_registry`/`prediction_logs`/`confidence_outcome_pairs`) → fitness/confidence + CF; optional Qwen rerank. Permissioned partner data only (`46` §9); fairness auto-halt (`46` §6).

## 7. How processed info reaches the frontend

Through existing editorial components (`60` §4), provenance shown: program/school detail = Qwen-synthesized facts; Match = Qwen scores + bands + net-price, Claude rationale beside; career/cost/visa = Qwen reference panels; search/feed = Qwen embeddings+rerank; change routing = Qwen `change_events` → Connect/alerts/notifications; **advisor chatbot = Claude** doing RAG over Qwen's index. Invariant: provisional + sourced + confidence + first-party-wins.

## 8. Embeddings — start here

Millions of embeddings needed; API embeddings costly at that volume (self-host pays off above ~10–15M/mo). Qwen3-Embedding is #1 MTEB-multilingual and via **Matryoshka emits exactly 1536 dims to match existing `Vector(1536)` columns — no migration, no re-embed.** Phase A: self-host/Bedrock the embedder, A/B retrieval vs current via `62`, promote. Pure backend, zero human-facing risk — the ideal first Qwen move.

## 9. Tuning (Qwen only)

Qwen LoRA/QLoRA (QLoRA fits bigger models on cheap GPUs), in ROI order: extraction → normalization/classification → scoring. Eval-gated (`62`): no regression + no fairness/safety failure ships; registered in `model_registry`/`training_runs`; A/B before promote. **Training data = the moat** (`07` §4.3, `46` §9): permissioned de-identified partner data + curated golden-set failures; **`consent.training=false` data NEVER trains** (hard gate). Claude agents are improved via the `61` loop (prompts/persona/RAG), **not** by swapping in Qwen — separate loops, both on `62`. Every tuned Qwen scoring checkpoint passes `46` §6 fairness before real cohorts.

## 10. Serving (`55`)

vLLM for Qwen (continuous batching); separate GPU worker fleet (bulkhead — never competes with API latency); batch where possible (extraction, featurization, embeddings) for GPU utilization. Start Bedrock-managed to defer ops; self-host once volume justifies. Quantization (AWQ/QLoRA) where eval holds quality. **Fallback:** Qwen serving down → processing degrades gracefully (queue+retry); **Claude conversation unaffected** — Qwen is never in the chat critical path.

## 11. Migration (backend-only)

A: embeddings (§8). B: crawler extraction (`60`), `62`-gated. C: normalization/classification + reranking + display synthesis. **(No Phase D.)** The human-facing layer is permanently Claude (§1) — no step moves the chatbot/advisory reasoning to Qwen. Each phase: Claude untouched; Qwen earns its processing role via `62`; `04` abstraction makes each promotion config.

## 12. Data, privacy & sovereignty

PII stays in-VPC: self-hosted Qwen processes profiles/documents/partner data **without a third-party model** — strengthens `46` + `consent.training` + stricter institutional DPAs. Claude (human-facing) still gets only consented, task-scoped, **PII-masked** context (`58`, `45` `consent_mask`); because Qwen does the PII-heavy bulk in-VPC, *less* sensitive data reaches the API.

## 13. Reuse existing scaffolding

`model_registry` (routing), `embeddings` + `student_feature_vectors` (`Vector(1536)` — Matryoshka match), `prediction_logs`, `training_runs` + `evaluation_runs` (shared with `62`), `drift_snapshots`, `ml_state`, `confidence_outcome_pairs`, `matching.py`. Work = wire serving + routing + Qwen tuning onto these.

## 14. Observability & SLOs (`55`/`62`)

GPU util + cost/day, Qwen latency p95 (batch/realtime), tokens by provider (`ai_turns`), embedding throughput, extraction F1 (`62`), display-synthesis voice+groundedness, Qwen uptime. SLOs: throughput targets; no processing-quality regression on Qwen migration (`62`); scoring checkpoints pass fairness; **Qwen outage never degrades the Claude conversation.**

## 15. Risks

GPU ops burden (mitigate: Bedrock first). Display-synthesis quality (gated by `62`; falls back to template/Claude if a type can't pass — still not a conversation). Tuning regress/bias (LoRA + eval-gate + fairness; never ship un-evaled). Embedding-dim lock-in (fix 1536). Don't over-build (RAG+prompts may suffice). **No quality risk to the conversation** — chatbot stays Claude, so the highest-stakes surface carries zero Qwen-migration risk (the main benefit of the boundary).

## 16. Acceptance

- [ ] **Hard boundary enforced**: no human-facing output served by Qwen; chatbot + `45` advisory = Claude (auditable via `model_registry` + `ai_turns` provider field).
- [ ] `04` lists Qwen as a backend transport; human-facing rows pinned to Claude.
- [ ] Qwen3-Embedding (1536d) serving; retrieval A/B via `62`; promoted on win.
- [ ] Processing pipeline (§5) end-to-end on Qwen with provenance.
- [ ] L3 uses Qwen embeddings + classical scoring; fairness-gated (`46`).
- [ ] Every tuned checkpoint: LoRA/QLoRA, consent-clean data (`46`), eval+fairness gated (`62`), registered.
- [ ] Display synthesis passes brand-voice + groundedness (`62`) before shipping.
- [ ] Qwen outage degrades processing gracefully, never breaks the Claude conversation.
- [ ] PII-heavy processing in-VPC on Qwen; Claude gets only masked/consented context.

## 17. Open questions

Bedrock-managed vs self-host (Phase A) — managed → self-host as volume grows. Qwen size per task (7/14/32B/MoE by `62`×cost). Embedding dim (confirm 1536). Display-synthesis scope (which content Qwen drafts vs templated/Claude — per-type via `62`; default Qwen structured+factual). **`04` needs Qwen registered as a provider with human-faces-Claude policy** (cross-ref, not edited here — `04` ≤30). Tuning-data pipeline under `46` consent tiers (own mini-spec). GPU capacity/autoscale (idle = main cost risk).

Sources: internal (`04`/`06`/`45`/`46`/`60`/`62` + `ml_loop`/`matching`). External: [Qwen3](https://qwenlm.github.io/blog/qwen3/) · [Qwen3-Embedding](https://qwenlm.github.io/blog/qwen3-embedding/) · [self-host vs API](https://www.helicone.ai/blog/self-host-llm) · [LoRA/QLoRA](https://effloow.com/articles/llm-fine-tuning-lora-qlora-guide-2026) · [vLLM](https://ardor.cloud/blog/vllm-production-deployment).
