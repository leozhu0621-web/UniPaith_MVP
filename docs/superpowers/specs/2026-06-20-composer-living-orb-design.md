# Composer Living Orb — Design Spec

**Date:** 2026-06-20 · **Status:** Approved (brainstorm) · **Surface:** `/s` chat conversation composer · **Source:** `frontend/src/pages/student/discover/UniConversation.tsx`

Completes the orb's state machine from the chat-tab spec (`2026-06-19-uni-chat-tab-redesign-design.md` §1) by giving Uni a **persistent living presence** at the composer, so the orb's states are actually reachable in normal use (not just per-turn).

## Goal

A small, always-visible orb at the left of the composer that reflects Uni's live state, so the surface feels alive and attentive — "motion = meaning" (§1). Idle is completely still; motion appears only with activity.

## Placement

A **24px `UniOrb`** at the **left edge of the composer**, before the paperclip/upload button, inside the existing input row. It is always visible (the composer is always present). The per-turn orbs on advisor messages stay as quiet history marks; this composer orb is the single *live* presence.

## State derivation

Derived from existing state in `UniConversation` — **no new state, no backend, no new props.** Priority order (first match wins):

| State | Trigger |
|---|---|
| `responding` | `streaming && streamText` — Uni's reply is streaming in |
| `thinking` | `turnMut.isPending \|\| (streaming && !streamText)` — awaiting / loading a reply |
| `celebrating` | a transient flag set for ~2s when `journey.matchesUnlocked` flips `false → true` (a real milestone, §1 "real milestones only") |
| `listening` | `draft.trim().length > 0` — the student is composing |
| `idle` | otherwise (still) |

The `celebrating` transient is the only added state: a `useEffect` watching `matchesUnlocked` sets a boolean true on the rising edge and clears it after ~2000ms (cleared on unmount). Reading-state stays in the upload panel (already shipped in #948); the composer orb does not duplicate it.

## Components / data flow

- A `useMemo` computes `composerOrbState: OrbState` from the vars above.
- A `useEffect` + `useState<boolean>` provides the transient `celebrating`.
- The composer row renders `<UniOrb state={composerOrbState} size={24} className="mt-0.5" />` before the paperclip.
- All tokens are already semantic (UniOrb uses brand tokens); light/dark safe.

## Testing

- Unit-test the pure state-derivation function (extract `deriveComposerOrbState({ streaming, streamText, pending, draft, celebrating })` so it's testable without rendering): asserts each branch + priority order.
- Existing `inline-enrich-card` test still green (renders UniConversation).

## Out of scope

`listening` as a typing *animation* beyond the orb's gentle pulse; sound; the per-turn orb behavior (unchanged); folder-reorder; "From My Space" upload option.
