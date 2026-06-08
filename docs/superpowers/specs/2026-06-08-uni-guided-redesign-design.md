# Uni — guided redesign (Discover → Uni) — Design

> **Status:** approved design (brainstorming output) · 2026-06-08
> **Surface:** `/s` (student Stage-01 Discovery)
> **Builds on:** the live Uni single-column conversation (PRs #322 + #328)
> **Source of truth for the journey:** `White-Paper/UniPaith-Whitepaper.html` → "User Experience & Method for Students" (three-stage student journey).

## 1. Goal

Two changes to the `/s` surface:

1. **Rename** the surface from **Discover → Uni** everywhere it appears as a label.
2. **Reshape the experience** to feel "like using AI, but much more guided": a ChatGPT/Claude-style two-pane workspace whose center conversation is **led stage-by-stage** through the white paper's Discovery layers, with a left rail that shows the journey + a live "what Uni knows" profile, ending in an **inline first look at matches** before handing off to Match.

Non-goals: changing the matching engine, the strategy artifact, the data model (no migration), or the Apply/Connect stages.

## 2. Chosen direction

From three explored directions (A guided-chat, B stepped-journey, C AI-workspace), the user chose **the UI of C with the experience of B**: a workspace shell (left rail) running a guided, stepped journey in the center.

Navigation model: **guided but revisitable** — Uni always leads you forward to the next thing; the rail lets you jump *back* to any completed stage to add/edit; stages *ahead* stay locked until reached.

## 3. Journey & IA (white-paper aligned)

The student journey in the white paper is three stages: **01 Discovery**, **02 Recommendation**, **03 Application Strategy & Support**. **"Uni" (`/s`) is Stage 01 Discovery.** Its rail leads through the three Discovery layers, then offers a first look at Stage 02, then hands off to Match.

| White paper | Uni rail item | Engine layer (existing) |
|---|---|---|
| Stage 01 · Profile Building | **About you** (basics · personality · self-identity — one flowing convo) | `discovery` profile (basic/personality/identity) |
| Stage 01 · Goal Setting | **Your goals** | `student_goals` |
| Stage 01 · Needs & Challenges | **What you need** | `student_needs` |
| Stage 02 · Recommendation | **inline "first look"** peek | `match_results` (fitness + confidence) |
| → go deeper | **Match** (`/s/explore`) | existing StrategyView + grid |

"About you" covers the three matching "tastings" (basic background, personality & behavior, self-identity) as **one flowing conversation**, not three visible sub-steps.

### Rename mechanics
- `StudentLayout` nav item: label `Discover → Uni` (Compass icon + `/s` route unchanged).
- `GlobalSearch` quick item: `Discover → Uni` (sub "Build your profile" → "Build your profile with Uni").
- `OnboardingPage` step title `Discover → Meet Uni`.
- Cross-page CTAs: "Open Discover" / "on Discover" → **"Talk to Uni"** / "with Uni" (`MatchesSection`, `StrategyView`, `CalendarPage` empty state, `FinancialAidPage`).
- `DiscoverHomePage` header eyebrow `Discover · with Uni → Uni`.
- Tab title (per-route titles from #356) for `/s` → "Uni".

## 4. The guided conversation (the "experience of B")

Each stage has the same rhythm:

- **Stage intro** — entering a stage, Uni opens with a one-line framing + an inviting first question. Never a blank slate.
- **Always a next move** — every Uni turn ends with a question and offers **2–3 LLM-suggested, contextual choice chips** + a standing "Uni, you suggest." Free-typing always available.
- **Earned Continue** — the "Continue to <next>" button appears only when the current stage's signal is strong enough (the engine's existing per-layer readiness in `completion_breakdown`). Until then Uni keeps gently leading. The student can still say "let's move on" and Uni obliges.
- **Reflect, don't interrogate** — Uni mirrors what it heard ("✓ Noticed…", the existing `NoticedCard`) so progress is visible and correctable.
- **Narrated transitions** — Uni hands off between stages in its own voice ("That gives me a real sense of you — now, what you need…").
- **Revisiting** — tapping a completed stage in the rail nudges the conversation ("Let's revisit your goals — anything to add or change?"); edits update the living profile live; stages ahead stay locked.

### Current stage = derived, not stored
The current stage is the **first not-yet-ready Discovery layer** in order (profile → goals → needs), derived server-side from `completion_breakdown`. No stage-pointer column. Revisiting is a conversational nudge, not a stored mode.

### LLM-suggested choice chips
The orchestrator returns **2–3 contextual suggested replies** with each assistant turn (in addition to the message). They are short, in-voice, and tuned to the current stage + what's still missing. Persisted in the assistant `discovery_message.extracted_signals` JSONB under a namespaced UI key (e.g. `{"_ui": {"suggested_replies": [...]}}`) so a reload keeps them — **no migration**. On generation failure, fall back to a small static per-stage chip set + "Uni, you suggest."

## 5. The inline "first look" (Stage 02 peek)

When `getHandoffVerdict().should_handoff` is true (all three layers have enough signal), the rail's "Your matches" unlocks and Uni **proactively delivers a first look in-thread** via a new `FirstLookCard`:

- A 1–2 sentence recap in Uni's voice of what it learned.
- **Top 2–3 fits** as compact rows: program name + the real **dual score** (fitness + confidence) + a one-line "why it fits" rationale.
- An honest note ("these sharpen the more we talk; there are more where these came from").
- Primary CTA **"Go deeper in Match →"** (`/s/explore`); secondary "Keep talking to Uni."

It **reuses** the matches API + dual scores + RationaleAgent. It does **not** rebuild the grid/filters/compare/strategy (that is what "go deeper" is for), and adds **no new tables/agents**. Re-openable anytime via the rail's "Your matches"; before unlock that item reads "unlocks once Uni knows enough." This evolves the existing `MatchHandoffCard`.

## 6. Living-profile rail + mobile

- **Desktop (≥ lg):** two-pane shell. Left **`JourneyRail`** = the journey stages (with progress/locked/done state) + the **living-profile panel** ("What Uni knows": grouped editable chips — lights you up / headed / need — a gap invitation, and "View full profile →" to `/s/profile`). Center = `UniConversation`.
- **Mobile:** one column. A **slim journey bar** pins to the top (current step + dot progress); tapping it slides down a sheet with the full stage list + living profile. The conversation owns the screen; chips, Noticed cards, and the first-look stack as on desktop.
- **One component, two homes:** the living profile is the existing `ProfileDrawer` content — docked in the rail on desktop, opened as a sheet on mobile. No duplicate code.

## 7. Architecture & components

**Reuse (already shipped):** unified `track="discovery"` session, orchestrator, extractor, per-layer validators, `completion_breakdown`; `UniConversation`, `NoticedCard`, `ProfileDrawer`, `noticed.ts`, `livingProfile.ts`; match data (`fitness_score`/`confidence_score`), matches API, RationaleAgent; Uni persona prompts.

**Add / change:**
- **Frontend**
  - `DiscoverHomePage` → two-pane workspace shell (rail + conversation) on desktop; journey-bar + sheet on mobile.
  - New `JourneyRail` (stages from `completion_breakdown` + progress + locked/done + the living-profile panel; clickable revisit for done stages).
  - `UniConversation` gains: stage header + progress bar, per-stage current-focus awareness, LLM-suggested chips rendering, the earned Continue gate, narrated-transition display.
  - `MatchHandoffCard` → `FirstLookCard` (recap + top-3 dual-score matches + rationale + go-deeper).
  - A `useJourneyState` hook deriving current stage / per-stage readiness / unlock from `completion_breakdown` + handoff verdict.
  - Rename across `StudentLayout`, `GlobalSearch`, `OnboardingPage`, cross-page CTAs, header, tab title.
- **Backend (orchestrator only; no schema change)**
  - The `"discovery"` branch becomes **stage-aware**: state header includes per-layer readiness + the current focus layer; the Uni playbook gains "lead the current layer; narrate transitions; offer Continue on readiness; on revisit, focus the named layer."
  - The assistant turn additionally returns **`suggested_replies`** (2–3), persisted in the assistant message's `extracted_signals._ui`.
  - All new behavior is behind a flag; the current open-discovery behavior is the fallback.

## 8. Data flow

Unchanged pipeline: turn → extractor → persist goals/needs/identity → validators → `completion_breakdown`. The frontend reads `completion_breakdown` (+ handoff verdict) to drive: rail progress, current stage, the Continue gate, and the first-look unlock. Suggested chips ride along on the assistant turn. **No new tables, no migration.**

## 9. Error handling & fallback

- Orchestrator failure (timeout/parse/guardrail) → existing rule-based fallback path; the conversation never 5xxs (preserve the Plan-2 integration invariant in `tests/test_plan2_integration.py`).
- Suggested-chips generation failure → static per-stage chips + "Uni, you suggest."
- First-look: if matches/rationale are unavailable, show the recap + "Go deeper in Match" without the inline rows (degrade, don't block).
- Flag off → the current live single-column-ish open Uni behavior (no regression).
- Preserve the workshop-no-generation contract (`tests/test_workshop_no_generation_contract.py`) — untouched here, but keep CI green.

## 10. Rollout

Gate the guided shell + stage-leading + chips behind a flag (e.g. `ai_uni_guided_v1`), current Uni as fallback. Ship dark, verify per-environment, then flip per the standing prod-flag practice. The rename is independent of the flag (safe to ship immediately) but ships together for a coherent release.

## 11. Testing

- **Frontend (vitest + `tsc -b` + `vite build`):** `JourneyRail` renders stages/progress/locked-done from `completion_breakdown`; Continue gate appears only on readiness; revisit nudges the conversation; `FirstLookCard` renders top matches + dual scores + go-deeper; mobile journey-bar opens the sheet; rename labels present; **all router-using components wrapped in `MemoryRouter` in tests; `setup.ts` network stub keeps unmocked calls synchronous** (lessons from #328).
- **Backend (pytest, `AI_MOCK_MODE`):** orchestrator leads the current layer, narrates a transition when a layer becomes ready, offers Continue, and focuses the named layer on revisit; returns 2–3 `suggested_replies`; flag-off returns the open behavior; the rule-based fallback never 5xxs. Extend the Uni eval (`ai/evals/uni_counselor.py`) with a stage-leading check.
- **Invariants:** Plan-2 fallback + workshop-no-generation contracts stay green.

## 12. Open questions

- Exact flag name + whether the rename ships flag-independent (proposed: rename ships immediately; guided behavior behind `ai_uni_guided_v1`).
- Whether revisiting a completed layer can *lower* its readiness (proposed: no — edits refine, never re-lock; the layer stays "done/revisitable").
- Whether the first-look should also tease the strategy narrative (proposed: no for v1 — keep it to top fits + recap; strategy lives in "go deeper").
