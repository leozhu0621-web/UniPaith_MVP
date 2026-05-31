# 37 · AI Extensibility — Assistive Layer for Admissions

> The contract for how AI plugs into procedural workflows. AI generates drafts and operational suggestions; humans keep final action. The principle that governs every AI-touched surface in `31`, `32`, `33`, `34`, `17`, `25`.
>
> Status: **draft v1.0** · 2026-05-29.

---

## 1. The principle (verbatim from Master Paper)

> "UniPaith's admissions workflows are designed around structured application records, standardized requirement checklists, and status-driven queues, so AI can be added as an assistive layer without changing the underlying admissions procedure. The AI layer is used to generate drafts and operational suggestions — such as packet summaries tied to specific evidence, pre-filled rubric-aligned notes, recommended queue prioritization, and message templates — while keeping final actions (status changes, communications, and decisions) under human control."

Three rules:
1. **AI generates drafts.** Never autonomous status changes, sends, or decisions.
2. **Every AI suggestion is reviewable.** Diff between AI version and human-edit version is captured in audit log.
3. **Failure is graceful.** Rule-based fallback per agent; UI shows "Showing rule-based result"; never 5xx.

---

## 2. Where AI plugs in

### 2.1 Drafts
- **Packet summary** (`32` §6) — `DraftSummarizerForReview` (Opus).
- **Rubric pre-fill** (`32` §6) — `AIPrefillForRubric` (Sonnet).
- **Decision notice draft** (`34`) — AI draft message before staff edits + sends.
- **Missing-items message** (`31`) — AI draft before send.
- **Interview-invite message** (`33`) — AI draft.
- **Clarification request** (`31` / `17`) — AI draft.
- **Inbox reply suggestion (student)** (`17`) — `InboxReplyDrafter`.
- **Campaign copy** (`25`) — `CampaignAudienceCopySuggester`.
- **Segment NL → rules** (`26`) — `SegmentBuilderNLBridge`.

### 2.2 Operational suggestions
- **Queue prioritization** (`31`) — AI-ranked priority queue.
- **Yield-risk alerts** (`31`) — AI-driven detection.
- **Intelligence digest** (`31`) — daily AI-narrated summary.
- **Drop-off diagnosis** (`28`) — AI-explained funnel drop.

### 2.3 Integrity / triage
- **Authenticity risk scoring** (`45` §18) on essays.
- **Document parse triage** (`45` §19).

---

## 3. Capture of human ↔ AI edit diff

For every AI surface above, the user can:
- Accept the AI suggestion as-is.
- Edit before saving/sending.
- Discard and start over.

Audit log records:
- `ai_generated:<surface>` event with the original AI output.
- `human_edit:<surface>` event with the diff at save/send time.
- `decision_action:<surface>` with the final action.

This diff is the training signal for future per-tenant prompt tuning.

---

## 4. AI assistant chat per applicant

Per `32` §6 — Q&A about the applicant. Sonnet. Persona = full applicant packet.

Sample questions reviewers ask:
- "What's their strongest signal?"
- "How does their math readiness compare to typical admits?"
- "Are there integrity concerns I should know about?"
- "What's the case against admitting?"

Answer always cites evidence from the packet; never invents.

---

## 5. Configuration

Per institution `/i/settings`:
- AI-assistive features on/off per surface.
- "No-training tier" override (per `46` §9) — block all data from training corpus.
- Per-surface confidence thresholds (e.g., only show AI prefill when confidence ≥ 70).

---

## 6. Brand compliance (cross-cutting)

Every AI surface follows:
- `AI assist` or `AI suggestion` badge per `02-design-system.md` §15.
- Why-affordance for the suggestion's rationale.
- Editable; user has the final word.
- Confidence dot row (1-5 dots) where applicable.
- Failure: "Showing rule-based result" inline note.

---

## 7. Gaps (from `47`)

- G-AI4 (major): Authenticity risk scorer not built.
- G-AI5 (major): DraftSummarizerForReview needs explicit wiring to Opus per `45` §14.
- G-AI7 (minor): InboxReplyDrafter not built.

---

## 8. Tests

- For each AI surface: human edit diff captured + audit-logged.
- AI failure → rule-based fallback; no 5xx.
- Per-surface on/off toggles respected.
- AI assistant chat never invents facts not in the packet (citation required).

---

## 9. Open questions

- **Per-tenant prompt overlay.** Some institutions want their own rubric vocabulary. Phase 2 — per-tenant prompt fragments composed into the agent's system block.
- **Reviewer feedback on AI suggestions.** Capture thumbs up/down on each suggestion as ongoing signal for prompt quality.
- **Compliance audit packs.** Per Year 2 SOC 2 effort — generate quarterly AI-usage audit reports from the audit log.
