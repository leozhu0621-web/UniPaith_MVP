# 61 · Chatbot Training & Evaluation — Build Spec

> **Model boundary (per `63`):** the chatbot + all human-facing advisory agents are **Claude**, permanently, by policy. **Qwen is never the chatbot.** This doc's loop tunes the *Claude* conversation (prompt/persona/RAG); the *Qwen* backend is tuned separately (`63` §9). Both ride the shared eval harness (`62`).
>
> Buildable spec for getting the two conversational Claude agents — **student advisor** (`19`, `ai/orchestrator.py`) and **faculty/institution assistant** (`37`, `ai/review_assist.py`/`institution_reply.py`) — to a measured behavior + performance standard via a **continuous, proactive, eval-driven** loop. Grounded in the real `ai/` modules (`prompts/*.md`, `evals/runner.py`, `agent_registry.py`). "Training" = prompt/persona/RAG improvement under eval gates (Claude is steered, not fine-tuned). Standards from the materials (Master Paper voice, Business Methodology, Prompt Library, brand `01` §6).
>
> Status: **draft v2.0** · 2026-05-30 · v2 converts standards → build tasks against real modules.

---

## 1. What exists vs what to build

| Piece | Real today | Status |
|---|---|---|
| Agent prompts (the levers) | `ai/prompts/*.md` (21 incl. `orchestrator_discovery.md`, `workshop_*.md`, `rationale.md`) | exists |
| Orchestrator (advisor) | `ai/orchestrator.py` (`_build_discovery_system_prompt`, `Orchestrator`) | exists |
| Eval harness | `ai/evals/runner.py` + `ai/evals/fixtures/` | exists — extend to the `62` shared harness |
| Agent→tier registry | `ai/agent_registry.py` (`AGENT_TIERS`) | exists |
| Provider abstraction | `ai/providers/` | exists |
| Behavior constitution (per-agent) | partial (inside prompts) | **formalize as `ai/prompts/_shared/constitution_*.md`** |
| Golden set (versioned) | `ai/evals/fixtures/` (seed) | **grow + version** |
| Calibrated LLM judge | — | **NEW (`62`)** |
| Red-team / synthetic battery | — | **NEW (`62` §7)** |
| Production sample→judge loop | — | **NEW** |

So the scaffolding exists; this builds the **constitution, golden set, judge, and the continuous loop** on top of `ai/evals/`.

---

## 2. "Training" without fine-tuning (the levers, all real files)

Claude is improved via levers we control — **not** weights:
1. **System prompt / constitution** — `ai/prompts/orchestrator_discovery.md` + a new `_shared/constitution_student.md` / `_shared/constitution_faculty.md` (§3).
2. **Persona config** — the persona block builders in `ai/orchestrator.py` (profile + signals).
3. **RAG grounding** — retrieval over the `60`/`63` knowledge graph so answers cite real data.
4. **Few-shot exemplars** — curated good/bad turns in the prompt.
5. **Tool design** — the agent's tool schemas (`ai/tools/`).

Loop = **eval-driven development**: define standard → measure (`62`) → improve a lever → re-measure → ship on no-regression. Fine-tuning is last-resort and **only on Qwen** (`63`), never the Claude path.

---

## 3. Behavior constitution (build as versioned files = the rubric)

Per-agent constitution in `ai/prompts/_shared/constitution_{student,faculty}.md`, version-tagged, loaded into the system prompt **and** used verbatim as the `62` judge rubric (one source of truth). Dimensions sourced from the materials:
- **Voice & tone** (`01` §6): warm, literal, encouraging, never marketing-hype; "explain everything" (`07` §2).
- **Groundedness:** cite real data (RAG over `60`); "I don't have current data on X" over fabrication.
- **Role adherence:** advisor counsels a student; faculty assistant supports staff — neither crosses over.
- **Scope:** helps discovery/fit/application; does **not** write essays (`14` no-generation, enforced by `guardrail_service.py`), does **not** promise admission, does **not** give deterministic admit/deny.
- **Fairness:** no protected-class proxies (`46` §6).
- **Safety + crisis** (§4).

Build task: extract the implicit rules already in `orchestrator_discovery.md` into the constitution files; reference them from the prompt via the `_shared` include pattern.

---

## 4. Safety & crisis escalation (hard floor)

- Crisis-signal detection (self-harm, abuse, acute distress) → empathetic response + **escalate to human/crisis resources**; never clinical counseling. Build `ai/safety.py` (signal classifier + escalation response template) called in the orchestrator turn pipeline.
- Refuse + redirect on out-of-scope/harmful asks (jailbreaks, "write my essay", "guarantee admission", PII extraction) — partly covered by `guardrail_service.py`; extend.
- These are **hard-floor** dimensions in `62` — any failure blocks a release; any red-team pass blocks.

---

## 5. Performance rubric (the `62` scored dimensions)

`groundedness · constitution-adherence · helpfulness · role/persona-adherence · safety(hard) · brand-voice · tone`, each 0–1 by the calibrated judge (`62` §4), **plus deterministic checks** (refusal correctness, PII-leak regex, no-generation assertion) that run before the LLM judge. Encoded as the chatbot adapter's `rubric()` in `62` §5.

---

## 6. Continuous loop (build on `ai/evals/`)

```
production conversation (ai_turns) → sample + judge (62 runner) → cluster failures
   → curate into golden set (ai/evals/fixtures, versioned) → improve a lever (§2)
   → CI-gate vs golden set (62 §6) → A/B (ab_test_assignments) → promote on no-regression
```
Runs continuously; the golden set only grows. The `ai/evals/runner.py` is the seed — extend it to the `62` shared harness via the chatbot adapter (`62` §5).

---

## 7. Proactive testing (don't wait for users to find failures)

- **Synthetic stress cases:** edge personas, off-scope asks, crisis-phrasing variants, multilingual — generated, run every release (`62` §7).
- **Red-team battery:** jailbreaks, essay-writing coercion, admit/deny pressure, PII extraction, bias probes — committed under `ai/evals/fixtures/redteam/`; any pass blocks release.
- **Coverage-gap mining:** cluster real `ai_turns` (embeddings); thin/low-score clusters → new synthetic cases + fixes.

---

## 8. Outcome linkage

Tie conversation quality to downstream outcomes where lag allows (advised student completed profile / applied / enrolled); fast-loop proxies = 👍/👎 (`ai_turn_feedback` table + `ai/` feedback wiring), escalation rate, resolution. Feeds which levers to prioritize.

---

## 9. Per-agent specifics

- **Student advisor** (`19`, `ai/orchestrator.py`): streaming (`45` §25), artifact-aware (updates the discovery rail), profile-grounded — highest-stakes surface; protect it.
- **Faculty assistant** (`37`, `ai/review_assist.py` + `ai/institution_reply.py`): applicant-context-grounded, rubric-aware, **drafts never decides** — humans keep final action.

---

## 10. Build tasks (checklist)

- [ ] `ai/prompts/_shared/constitution_{student,faculty}.md` (versioned) — extracted from existing prompts; wired into prompt + `62` rubric.
- [ ] `ai/safety.py` crisis classifier + escalation; called in the turn pipeline; hard-floor in `62`.
- [ ] Chatbot adapter in `62` (produce/rubric/materialize) reusing `ai/evals/runner.py`.
- [ ] Grow + version `ai/evals/fixtures/` golden set from real failures; `redteam/` battery.
- [ ] Production sample→judge job (`55` §4 queue) writing scores to `evaluation_runs`.
- [ ] Deterministic checks (refusal/PII/no-generation) before LLM judge.
- [ ] A/B prompt/persona variants via `ab_test_assignments`; promote on no-regression.
- [ ] Wire 👍/👎 (`ai_turn_feedback`) into the curate step.

---

## 11. Acceptance

- [ ] Per-agent constitution files exist, versioned, and ARE the `62` rubric.
- [ ] Safety/crisis hard-floored in `62`; red-team battery blocks release on any pass.
- [ ] Continuous sample→judge→curate→improve→gate loop runs (on `ai/evals/`).
- [ ] Golden set grows from real failures; CI-gated; A/B before promote.
- [ ] No-generation (`14`) + no-admit/deny + no-fabrication enforced (deterministic + judge).
- [ ] Both agents Claude (no Qwen in the conversation, per `63`); verifiable via `ai_turns.provider`.

---

## 12. Open questions

- Multilingual standard (top-5 markets) — verify Claude quality per language (`45` §27); add per-language golden cases.
- Human-review sampling rate + staffing (shared with `60`/`62`).
- Build-vs-buy the judge/runner — `62` §13 (recommend extend `ai/evals/runner.py`, optionally DeepEval primitives).
