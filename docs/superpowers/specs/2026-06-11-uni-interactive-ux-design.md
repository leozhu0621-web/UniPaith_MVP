# Uni — motivated, interactive, visual UX — Design

**Date:** 2026-06-11
**Status:** Approved (4/4 directions selected by the user). Phase 1 ships frontend-only; Phase 2 adds a small orchestrator hint.
**Surface:** `/s` → `DiscoverHomePage` (two-pane: `JourneyRail` + `UniConversation`).

> **Goal:** make the Uni discovery experience feel motivated and interactive — not "just talking" — with strong, on-brand visual effect. Reuse the existing design system (semantic tokens, `--ease/--dur` motion tokens, the earned-gold `animate-beat`, the density layer) and the orchestrator signals the frontend already receives (`suggested_options`, `requested_layer_advance`, `completion_breakdown`, "noticed" signals). Ship to prod.

---

## Principles (kept)
- Conversation stays the hero; interactivity *augments* it, never replaces typing ("…or just tell Uni" is always present).
- **Gold = earned beat only** (`animate-beat` / `elev-glow`). Cobalt (`secondary`) = in-progress / interactive. Never decorative.
- Respect `prefers-reduced-motion` (already gated in `UniConversation.canStream`; reuse for the new motion).
- No new backend in Phase 1; Phase 2 is a tiny additive signal (no migration).

---

## Phase 1 — frontend only (ships first)

### 1.1 Richer Profile · Goals · Needs stepper — `JourneyRail.tsx`
Today: three stage rows with a dot (done/current/locked) + "now". No progress shown.
Change: each stage row gains a thin **per-stage progress fill** using `stage.pct` (cobalt `bg-secondary`, `h-1 rounded-full bg-muted` track, width `pct*100%`, `transition-[width] duration-[--dur-slow] ease-[--ease-out]`), and the dots are joined by a short vertical **connector** (a 2px `bg-border` line behind the dot column, cobalt up to the current stage). Keep `StageDot` states and revisit-on-done behavior. The in-conversation header bar in `UniConversation` (lines 311–326) stays but is de-duplicated to a single thin "current stage" affordance (the rail owns the full stepper).

### 1.2 Milestone celebration beats — new `useMilestoneBeat` + `JourneyRail` + `FirstLookCard`
New hook `discover/useMilestoneBeat.ts`: given `stages` + `matchesUnlocked`, track the previous values in a ref and return `{ newlyDone: Set<StageKey>, matchesJustUnlocked: boolean }`, auto-clearing after `--dur-slow` (360ms) via a timeout. Pure client; no data change.
- In `JourneyRail`: when a stage is in `newlyDone`, add `animate-beat` to its `StageDot` (one gold pulse). When `matchesJustUnlocked`, add `animate-beat` + `elev-glow` to the "Your matches" row and swap its copy to a brief "Unlocked" state.
- In `FirstLookCard`: the **ready** state is the reward — switch its container from cobalt (`border-secondary/30 bg-secondary/5`) to the gold earned treatment (`card-accent`: `border-2 border-primary elev-glow`) and fire `animate-beat` once on the first ready render (track with a ref). The not-ready "always" card stays cobalt/neutral (not an earned moment).

### 1.3 Animated "Noticed" + living-profile counter — `NoticedCard.tsx` + `JourneyRail.tsx`
- `NoticedCard`: add `animate-slide-up-fade` on the card (fresh DOM node per new message → plays naturally), a small **`+N`** badge (N = `items.length`) next to "Noticed", and a one-time cobalt tick. Items render in a `stagger-list` so chips cascade in.
- Counter: in the rail's "What Uni knows about you" header, show a live count = `livingProfile.lightsUp.length + goals.length + needs.length`. When it increases between renders (ref-tracked `prevCount`), apply `animate-beat` to the count badge (a small gold pulse — an earned "you taught Uni something" beat). `JourneyRail` queries `getLivingProfile` (same `['discovery','livingProfile']` key already in flight) for the count.

### 1.4 Tap-to-answer choice cards — `UniConversation.tsx`
Replace the chip row (lines 415–428) with a new `discover/AnswerChoices.tsx`:
- When `llmChips.length > 0` (the orchestrator's `suggested_options`), render them as **warm choice-cards**: full-width-ish, `rounded-lg border border-border bg-card px-3 py-2 text-sm`, left a small `+`/dot, hover `-translate-y-px border-secondary/40` (`--dur-fast`), single-tap → `send(option)`. Stagger their entrance.
- The `QUICK_REPLIES` fallback ("I'm not sure where to start", etc.) is demoted to subtle text "ways in" (tiny muted links under the input), visually distinct from real answer options so the choice-cards read as *the* answer.
- Typing (textarea) is unchanged and always available.

### Phase 1 testing
- `tsc -b` clean; `vitest` green (existing `discover-home.test.tsx` + a new `uni-interactive.test.tsx`: choice-cards render from `suggested_options` + single-tap sends; NoticedCard shows `+N`; `useMilestoneBeat` flips on transition).
- Honor `prefers-reduced-motion`: all `animate-*` classes are `motion-safe:` prefixed (or gated) so reduced-motion users get the structure without the motion.

---

## Phase 2 — intentional affordances (small orchestrator hint, no migration)

The orchestrator currently sends `suggested_options: string[]`. Add an **optional** sibling field in the same `extracted_signals` JSONB (no migration; the field is additive and ignored by old clients):

```
suggested_input?: {
  kind: 'choice' | 'multi' | 'scale',
  options?: string[],          // choice/multi
  low_label?: string,          // scale
  high_label?: string,         // scale
  signal_hint?: string,        // e.g. "staying near family" (for scale → need severity)
}
```

- Backend: `unipaith-backend` orchestrator (the discovery system prompt + the response assembly) may set `suggested_input` when a question is naturally a pick-many or a 1–5 importance question (needs severity). Deterministic fallback never sets it (frontend defaults to single-choice cards). Behind the existing discovery flag; rule-based path unaffected.
- Frontend `AnswerChoices` reads `suggested_input.kind`:
  - `choice` (default) → the Phase-1 choice-cards.
  - `multi` → multi-select cards + a cobalt **Continue** that sends the joined selection.
  - `scale` → a 1–5 **importance slider** (`low_label`/`high_label`), sends e.g. "Staying near family — must-have." Maps to the needs severity vocabulary (`must_have | strong_preference | nice_to_have`).
- Types: add `SuggestedInput` to `types/index.ts` under `AssistantTurnSignals`.

### Phase 2 testing
- Frontend: `AnswerChoices` renders the right control per `kind`; multi-select Continue sends joined text; slider sends the mapped severity phrase.
- Backend: orchestrator may emit `suggested_input`; integration test asserts the rule-based path never emits it and the LLM path's emission is schema-valid; the existing "never 5xx / falls back" invariant holds.

---

## Files

| File | Phase | Change |
|---|---|---|
| `discover/JourneyRail.tsx` | 1 | per-stage `pct` fills + connector; milestone beats on dots + matches row; "what Uni knows" counter w/ beat |
| `discover/useMilestoneBeat.ts` | 1 | **new** — transition detector (newlyDone / matchesJustUnlocked), auto-clears |
| `discover/NoticedCard.tsx` | 1 | slide-up entrance, `+N` badge, staggered chips |
| `discover/FirstLookCard.tsx` | 1 | ready state → gold `card-accent`/`elev-glow` + one-time `animate-beat` |
| `discover/AnswerChoices.tsx` | 1 (+2) | **new** — choice-cards (P1); multi/scale via `suggested_input` (P2) |
| `discover/UniConversation.tsx` | 1 | use `AnswerChoices`; demote `QUICK_REPLIES`; de-dupe header bar |
| `test/uni-interactive.test.tsx` | 1 | **new** — choice-cards, NoticedCard +N, useMilestoneBeat |
| `types/index.ts` | 2 | add `SuggestedInput` on `AssistantTurnSignals` |
| `unipaith-backend` orchestrator | 2 | optionally emit `suggested_input` (LLM path; rule-based never) |

## Open questions (deferred, non-blocking)
- The "what Uni knows" count uses living-profile composition (goals+needs+lightsUp); if a richer "signals learned" count is wanted later, derive from `completion_breakdown` deltas.
- Phase 2 `scale` → needs-severity wording: confirm the exact phrase the orchestrator extractor expects so the slider answer round-trips into `student_needs.severity`.
