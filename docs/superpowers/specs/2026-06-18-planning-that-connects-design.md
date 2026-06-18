# Planning that connects — "Your plan" overview (design)

**Date:** 2026-06-18 · **Status:** Approved by founder (mockup approved) · **Scope:** frontend-only, no API/schema change

## Problem
The Planning cluster is four disconnected CRUD tabs — Strategy · Goals · Needs · Preferences. The dependencies between them are invisible: Goals feed Strategy (you can't generate a strategy without an active academic goal, and nobody says so); Needs + Preferences shape Matches. A student edits four separate lists with no sense that they form one plan.

## Solution
Fold a connected **"Your plan"** overview into the **top of the Strategy tab** (Planning still opens to `?tab=strategy`; no new tab). The existing strategy detail (action buttons, ApplicationGamePlan, active/draft/archived StrategyCards, editor) stays below, unchanged.

The overview has two parts:

### 1. The chain
A horizontal flow of four linked nodes making the "feeds into" relationships explicit:

`Goals → Strategy → Needs & prefs → Matches`

Each node: an icon, a live count, and a one-line connection hint; clicking deep-links to that piece.
- **Goals** — count of active goals (and active *academic* goals). → `/s/profile?tab=goals`
- **Strategy** — the active strategy summary (career → degree, `v{version}`), or "none yet". This is the current tab — the "you are here" anchor (not a link, or scrolls to the detail below).
- **Needs & prefs** — count of needs (+ must-haves); preferences set/incomplete. → `/s/profile?tab=needs`
- **Matches** — count of matches + top fit %; teal accent (not gold). → `/s/explore`

A caption underneath: "Goals shape your strategy. Your needs & preferences shape your matches."

### 2. Sharpen your plan
A short, derived list of the real gaps — surfacing exactly the hidden dependencies, each a one-tap link (show-don't-tell). Render only the gaps that actually apply:
- No active academic goal → "Add an academic goal to generate a strategy" → `?tab=goals`
- Strategy is a stub/preview or absent → "Your strategy is a preview — develop it with Uni" → `/s?intent=strategy`
- No needs mapped → "Map what you need to sharpen matches" → `?tab=needs`
- Preferences incomplete (no budget / funding) → "Set your preferences to sharpen matches" → `?tab=preferences`
- Only academic goals, no social/personal → "Add a social or personal goal" → `?tab=goals`

If nothing applies, the section hides (don't invent a gap).

## Data (all existing endpoints — compose like the Home page does)
`getActiveStrategy()` (`['strategy','active']`, shared with StrategyTab) · `listGoals()` · `listNeeds()` · `getPreferences()` · `getMatches()` (`['matches']`). No backend or schema change.

## Voice / brand
Dense, editorial, semantic tokens (dark-mode safe). Matches accent is teal, **gold stays reserved** for earned milestones. The chain nodes reuse the StatTile/ListRow density idiom; the sharpen list is ListRow + arrow. No manufactured cheer.

## Out of scope
No new tab, no changes to the four detail tabs, no backend. Only `StrategyTab.tsx` gains a top overview component (`strategy/PlanOverview.tsx`).

## Verification
tsc 0 · vite build 0 · eslint 0 errors · existing strategy tests stay green · one quick visual check of the folded overview, then ship.
