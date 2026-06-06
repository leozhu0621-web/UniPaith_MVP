# Discover Redesign — "Uni," a real college-counselor conversation

> Status: **design approved** · 2026-06-06 · Surface: `/s` (Discover, Stage 1) · Persona: **Uni**

## 1. Problem

The current Discover experience fails on four fronts (all confirmed by the user):

1. **Interrogation, not conversation** — question → answer → next question. A Q&A form wearing a chat skin.
2. **Too much UI around the chat** — track tabs, layer pills, progress %, a strategy-CTA bar, and readiness + artifact rails all compete with the actual talking.
3. **Rigid/confusing structure** — the student must pick a track (Profile / Goals / Needs) and a layer (basic / personality / identity), pushing the system's mental model onto an anxious applicant.
4. **Cold / robotic** — it doesn't feel warm, personal, or motivating; nothing makes a nervous student want to open up.

## 2. Vision

Discover becomes **one warm conversation with Uni — a real college counselor** — plus a **quiet, living profile** the student can peek at. Uni guides the way a skilled human counselor actually does. The cluttered, track-based UI is gone; the underlying signal model (goals / needs / identity) and the matching engine are unchanged.

**North star:** a nervous applicant opens Discover and feels like they're talking to a calm, sharp counselor who *gets* them — not filling out a form.

## 3. Design

### 3.1 Uni — persona & voice

- **Name:** Uni. Avatar "U". Warm, professional, **composed** — a real college counselor.
- **Voice:** acknowledge → ask; collaborative ("we"); one thing at a time. **No slang, no "lol," no emoji-speak, no over-familiar register.** (Grounded in `Instructions/student_emotional_design_system.md`: "warm curiosity," micro-confirmations, every inference editable.)

### 3.2 Uni's counselor playbook (the agent contract)

Uni is trained to **follow the real actions of a human college counselor**. This becomes her system prompt **and** a constitution + eval set.

**Uni always:**
- Builds rapport & safety first — introduces herself, sets expectations, normalizes "no wrong answers."
- Asks **open** questions about **concrete moments**, not abstract traits ("when did you feel absorbed?" not "are you analytical?").
- **Reflects back** the student's own words before going deeper (active listening).
- **Validates & normalizes** — eases anxiety, never judges.
- Probes **one layer at a time**, then **offers perspective/options** like a counselor guiding — not just firing questions.
- **Summarizes & checks** ("So it sounds like…") and ties back to fit/thriving.

**Uni never:**
- Uses slang / "lol" / emoji-speak / over-familiar register.
- Interrogates (rapid-fire Q→A→Q with no reflection).
- Asks more than **one** real question per turn.
- Judges, pressures, or uses ranking/anxiety language.
- Dumps a wall of buttons (quick replies are gentle fallbacks only).

### 3.3 The conversation UX (single column)

- **Layout:** single centered column. Only chrome is an eyebrow ("Discover · with Uni") and a quiet **"✦ Your profile ▸"** link. No track tabs, layer pills, progress %, strategy CTA, or rails.
- **Opening (first run):** Uni introduces herself, names the goal ("find where you'll *thrive*, not just get in"), lowers the stakes, and asks **one** easy question. No prompt wall.
- **Turns:** warm bubbles (Uni left with "U" avatar; student right). Acknowledge → one question. Streaming "typing" dots while Uni responds.
- **Quick replies:** counselor-style ways-in for stuck students — "I'm not sure where to start," "Could you give an example?," "You ask me." Gentle fallbacks, not the primary interaction.
- **Inline "✓ Noticed…" cards:** as Uni learns something, a small confirmation card appears **in the thread** ("✓ Noticed: you're energized by hands-on problem-solving & building") with an **✎ tweak** to edit. Earned progress + micro-confirmation; every inference editable.
- **Composer:** clean single input ("Tell Uni what's on your mind…") + send.

### 3.4 The living profile — "✦ Your profile ▸"

Opens as a **slide-over drawer** within Discover (dismissible, keeps the conversation in context) — distinct from the durable `/s/profile` record. A **warm, editable reflection** of what Uni has learned:

- A short synthesized narrative in Uni's voice ("You come alive building things and solving hard problems…"), editable.
- Human-labeled sections (not Profile/Goals/Needs/layers): **What lights you up · Where you're headed · What you need to thrive** — chips, each editable, with "＋ add."
- **Gaps as gentle invitations**, never a progress bar or "incomplete": "Uni could understand you better if we talk about budget →" (links back into the conversation).
- Edits feed back into the same signal store → sharpen matches.

### 3.5 The match handoff (counselor-led)

Replaces the 50%-on-3-tracks gate + "Generate strategy" CTA.

- When Uni senses she has a real picture (the existing readiness/handoff signal), she **offers matches in the conversation**: a warm message + primary action **"See programs that fit me →"** and secondary **"Keep talking."**
- **Not a locked gate.** The student can request matches **any time**; Uni shows them with an honest confidence note ("these will sharpen the more we talk").
- "See programs that fit me" → the existing strategy/match flow (Explore).

## 4. Architecture / codebase mapping

### 4.1 Frontend (`frontend/src/pages/student/`)

- **Keep:** chat plumbing (TanStack Query, discovery session/message API), send/streaming states, the Explore/match surface, Profile as the durable record.
- **Replace:** `DiscoverHomePage.tsx` → single-column Uni layout (no rails); `discover/ChatPanel.tsx` → Uni conversation; `discover/`-EmptyState → Uni's warm opening.
- **Remove from Discover:** `TrackSelector`, the `LayerSwitcher`, `ReadinessRail` + `ArtifactRail` (from the main view), `StrategyHandoffCTA`.
- **Add:** inline editable "✓ Noticed…" cards; the living-profile drawer/view; the in-thread match-handoff card; Uni persona (avatar/name/voice).
- The removed widgets' data still lives on the **Profile page** (durable record) — only Discover's cluttered UI goes.

### 4.2 Backend (`unipaith-backend/src/unipaith/`)

- **Keep (data model unchanged):** `discovery_sessions` / `discovery_messages`; `student_goals` / `student_needs` / `student_identity`; the extractor / validator / judge; matching; strategy; feature flags + rule-based fallback.
- **Change:**
  - `ai/orchestrator.py` → **Uni counselor-playbook system prompt** (the always/never above).
  - **Extraction routed by content, not `session.track`** — today `discovery_service.py` routes signals by the session's track (profile→identity, goals/needs→those, lines ~287/675). A single track-less conversation must feed goals + needs + identity, so the extractor tags each turn's signals by **content/signal-type**. A single unified session (track-less or a new `"discovery"` track) backs the conversation.
  - Readiness/handoff surfaced as **Uni's offer** rather than a `%` gate (reuse the existing handoff verdict).
- **Add:** Uni's playbook as a constitution + eval cases, reusing the chatbot-eval / constitution infra (§61/§62) so we can **measure** counselor-like behavior before shipping.

### 4.3 Data flow

```
One Uni conversation
  → extractor (routes each turn by content)
  → goals · needs · identity   (existing stores)
        ├── read by  "✦ Your profile" (warm, editable)
        └── read by  matching engine → "See programs that fit me" → Explore
```

## 5. Error handling & fallback

- **LLM failure / flag off:** the existing **rule-based fallback** keeps Discovery working (Uni degrades to scripted-but-warm openers; replies still saved). A flag-off or extractor error never 5xxes the conversation (per the Plan-2 integration invariant).
- **Empty/blank states:** never a dead end — Uni always has a next gentle question; the profile view's gaps are invitations, not errors.
- **Editing:** inference edits are optimistic with server reconcile; failures show a recoverable inline note.

## 6. Testing

- **Agent behavior (eval):** counselor-playbook eval set — asserts open questions, reflection, one-question-per-turn, no slang/interrogation, safety-floor preserved. Gates in CI like the existing chatbot evals (deterministic, no key needed for the structural checks).
- **Extraction:** a single mixed conversation produces goals **and** needs **and** identity signals (content-routed), verified against the existing extractor contracts.
- **Frontend:** Discover renders single-column with no track/rail chrome; inline "Noticed" card appears + is editable; "✦ Your profile" opens the living view; handoff card routes to Explore. Vitest smoke + key-interaction tests.
- **Regression:** matching, strategy, and the Profile page still read the same signals unchanged.

## 7. Non-goals (YAGNI)

- No change to the matching engine, strategy generation, or the Profile page's durable record.
- No new data tables (reuse discovery + signal stores).
- No voice/audio, no multi-counselor characters — one persona (Uni).
- Not removing tracks from the **data model** — only from the **student-facing UI**.

## 8. Open questions

None blocking. Persona (Uni), voice (composed counselor), structure (single-column + quiet living profile + counselor-led handoff), and the backend mapping (content-routed extraction) are all resolved.
