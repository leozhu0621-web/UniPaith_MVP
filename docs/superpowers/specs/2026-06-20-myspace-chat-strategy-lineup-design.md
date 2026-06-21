# My Space ↔ Chat tab — strategy lineup (design)

**Date:** 2026-06-20 · **Status:** Approved by founder (design + mockup approved) · **Scope:** strategy first (Phase 1), then extend the pattern (Phase 2)

## Problem
The redesigned Chat tab (`/s`) is a session + **template runner** of guided work-orders whose steps are either **prompts** (render a widget, write live via `setEnrichValue` — real) or **actions** (`generate_strategy`, `build_school_list`, `generate_needs_map`, …; 9 in `ACTION_CATALOG`). The runner's action steps are **explicit placeholders** ("Uni is building…", no real artifact). My Space holds the **real** versions (Strategy tab's `StrategyService.generate` → `StudentStrategy`; real Goals/Needs/Matches). So the founder's locked architecture — **the chat FILLS; My Space is the structured HOME** — isn't wired: the chat *pretends* to build strategy, the real artifact lives only in My Space, and the two don't converge.

Note the asymmetry to exploit: the Uni **managed agent** already has a *real* `generate_strategy` tool (`uni_tools.py:248` → `StrategyService(db).generate(user_id)`). The real service exists; this is wiring + convergence, not new ML.

## Phase 1 — Strategy (build now)

### A. Make the chat's `generate_strategy` action real, hosted in My Space
- **Backend — action-run endpoint.** Add `POST /students/me/chat/actions/{action_key}/run` (in `api/chat_*`) that dispatches by `action_key`. For `generate_strategy` it calls the existing `StrategyService.generate(user_id)` (same path the agent + the Strategy tab use) → the one active `StudentStrategy` → returns an `ActionArtifact { status:"done", title, summary, link:"/s/profile?tab=strategy" }`. Other `ACTION_CATALOG` keys return `status:"not_ready"` (honest placeholder) until Phase 2 — no fabricated data. Reuse `ACTION_KEYS` for validation (404 on unknown).
- **Frontend — runner calls it.** `TemplateRunner` action steps call the new endpoint (replacing the fixed-delay placeholder) and render the returned `ActionArtifact` — the real strategy summary (career → degree + one-line angle) + "Open in My Space → Strategy". Keep the "Uni is building…" pending state while it runs.
- **One artifact, two surfaces:** the action writes the same `StudentStrategy` My Space reads (`['strategy','active']`), so the Strategy tab auto-reflects it. No new data model.

### B. My Space ← chat handoff
- The Strategy tab's **"Develop with Uni"** stops navigating to the old `/s?intent=strategy`. Instead it `createSession({ template: 'sharpen_strategy', origin_kind: 'template' })` (existing `chatSessions.createSession`) then navigates to `/s` so the **"Sharpen your strategy" template runner** opens. (Confirm the create-session param that selects a template; if absent, add a `template_key` param — small, additive.)

### C. Strategy tab → white-paper framing (frontend, reuse existing data)
Reframe `StrategyTab` (keep the `PlanOverview` "Your plan" chain on top):
- **Your angle** — career_target → target_degree + the narrative; the 3 paths (academic/financial/geographic) become supporting chips/detail, not the headline.
- **Your school list** — the recommended programs from `['matches']` as cards, each carrying **two separate word-tags**: a **Fitness** tag from `fitness_score` (Excellent / Strong / Good / Moderate / Low fit) and an **Odds** tag from the admission-likelihood signal (use `confidence_score` as the current proxy — implementer confirms whether a dedicated likelihood exists — worded Safe / Likely / Toss-up / Reach / Long shot), plus a one-line reason. Plain words, no bars/tables (locked brand). A "See all matches in Discover" link. Fit and odds are independent — a reach can be a great fit.
- Two small shared helpers `fitWord(score)` + `oddsWord(score)` so the chat's inline plan card and this tab render the tags identically.

## Phase 2 — extend the pattern (after strategy ships)
Same "wire the action to the real service → return a real `ActionArtifact` → land in the matching My Space tab" for: `generate_goal_stack`→Goals · `generate_needs_map`→Needs · `build_school_list`→Saved/Matches · `build_checklist`→Applications · `compare_schools`→Offers/Saved compare · `draft_feedback`/`interview_practice`→Prep · `find_events`→Discover. Each reuses an existing service; each artifact links to its My Space home. Sequenced one at a time; not in Phase 1.

## Out of scope
No change to the matcher math, the StrategyAgent, the chat session/folder model, or the widget language (already aligned via the shared `EnrichWidget`). No new strategy data model.

## Verification
Backend: action-run endpoint dispatches generate_strategy to the real service (tests); unknown/other actions handled honestly. Frontend: tsc/build/eslint/vitest. Mock-user: run "Sharpen your strategy" in the chat → a real `StudentStrategy` is produced → it appears in My Space's reframed Strategy tab; the school list shows separate fit/odds word-tags. Ship via `/ship`; confirm live.
