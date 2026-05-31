# 61 · Chatbot Training, Evaluation & Continuous Improvement

> **Model note (per `63`):** the chatbot + all human-facing advisory agents are **Claude** — permanently, by policy. **Qwen is never the chatbot** (open-source Qwen is the invisible ML backend; it does not interact with humans). This doc's improvement loop tunes the *Claude* conversation (constitution, prompts, persona, RAG); the *Qwen* backend is tuned separately in `63` §9. Both share the eval harness (`62`).

> How the two conversational agents — the **student advisor** (`19`) and the **faculty/institution assistant** (`37`) — reach and keep a measured behavior + performance standard through a **continuous, proactive** loop. "Training" = eval-driven prompt/persona/RAG improvement (Claude isn't fine-tuned; it's steered). Standards come from the materials (Master Paper voice, Business Methodology, Prompt Library, brand `01` §6).
>
> Status: **draft v1.0** · 2026-05-30 · Production track. Pairs with `45` (the agents), `62` (the shared eval harness), `46` (fairness/safety), `19`/`37` (surfaces).

---

## 1. "Training" without fine-tuning

Claude is improved via **the levers we control**: system prompt / constitution (§2), persona config (`45`), RAG grounding (`60`/`63` knowledge graph), few-shot exemplars, tool design — **not** weight fine-tuning. The loop is **eval-driven development**: define the standard → measure → improve a lever → re-measure → ship on no-regression. Fine-tuning is last-resort and only on Qwen (`63`), never the human-facing Claude path.

## 2. Behavior constitution (the standard)

A written constitution per agent — the rubric the judge (`62`) scores against — sourced from the materials:
- **Voice & tone** (`01` §6): warm, literal, encouraging, never marketing-hype; "explain everything" (`07` §2).
- **Groundedness**: answers cite real data (RAG over the `60` graph); "I don't have current data on X" instead of fabricating.
- **Role adherence**: advisor counsels a student; faculty assistant supports staff — neither does the other's job.
- **Scope**: helps with discovery/fit/application; does NOT write essays (`14` no-generation), does NOT promise admission, does NOT give a deterministic admit/deny.
- **Fairness**: no protected-class proxies in advice (`46` §6).
- **Safety + crisis** (§3).

## 3. Safety & crisis escalation (hard floor)

- Detect crisis signals (self-harm, abuse, acute distress) → respond with empathy + **escalate to human/crisis resources**; never attempt to counsel clinically.
- Refuse + redirect on out-of-scope/harmful asks (jailbreaks, "write my essay", "guarantee I get in", PII extraction).
- These are **hard-floor** dimensions in `62` — any failure blocks a release.

## 4. Performance rubric (scored dimensions)

groundedness · constitution-adherence · helpfulness · role/persona-adherence · **safety (hard)** · brand-voice · tone. Each scored 0–1 by the calibrated judge (`62` §4) + deterministic checks (refusal correctness, PII-leak regex, no-generation).

## 5. Continuous loop

production conversation → sample + judge (`62`) → cluster failures → curate into the golden set → improve a lever (prompt/persona/RAG/exemplar) → CI-gate vs golden set → A/B → promote on no-regression. Runs continuously; the golden set only grows.

## 6. Proactive testing (don't wait for users to find failures)

- **Synthetic stress cases**: edge personas, off-scope asks, crisis-phrasing variants, multilingual — generated, run every release (`62` §7).
- **Red-team battery**: jailbreaks, essay-writing coercion, admit/deny pressure, PII extraction, bias probes — any pass blocks release.
- **Coverage-gap mining**: cluster real traffic; thin/low-score clusters get new synthetic cases + fixes.

## 7. Outcome linkage

Where lag allows, tie conversation quality to downstream outcomes (did the advised student complete profile / apply / enroll); use proxies (👍/👎 `ai_turn_feedback`, escalation rate, resolution) for the fast loop.

## 8. Per-agent specifics

- **Student advisor (`19`)**: streaming, artifact-aware (updates the discovery rail), profile-grounded; the highest-stakes surface — protect it.
- **Faculty assistant (`37`)**: applicant-context-grounded, rubric-aware, drafts (never decides); humans keep final action.

## 9. Acceptance

- [ ] Constitution written per agent; is the `62` rubric.
- [ ] Safety/crisis = hard-floor in `62`; red-team blocks release.
- [ ] Continuous sample→judge→curate→improve→gate loop running.
- [ ] Golden set grows from real failures; CI-gated; A/B before promote.
- [ ] No-generation (`14`) + no-admit/deny + no-fabrication enforced.
- [ ] Both agents Claude (no Qwen in the conversation, per `63`).

## 10. Open questions

- Multilingual standard (top-5 markets) — verify Claude quality per language (`45` §27).
- Human-review sampling rate + who staffs it (shared with `60`/`62`).
- **Cross-doc (RESOLVED):** the shared eval-harness is `62`; this chatbot loop plugs in via the chatbot adapter (`62` §5); `60` §13B extraction plugs in via the extraction adapter.
