# My Space v2 — rail tree + Strategy feature (design)

**Date:** 2026-06-15 · **Status:** Approved by founder (this session) · **Builds on:** `2026-06-10-my-space-design.md`

## Summary

Two related changes, shipped in order:

- **Ship A — IA restructure.** The My Space left rail becomes an **expandable tree**
  (Overview · Profile▾ · Saved▾ · Workspace▾), and **Messages** is promoted to a
  top-level nav tab between Discover and My Space.
- **Ship B — Strategy feature.** The thin read-only Profile › Strategy tab becomes a
  **living strategy doc**: editable narrative + three path tracks, version history,
  AI regenerate, a "Develop with Uni" hook (future skill), and an **Application
  game-plan** sub-section (reach / target / safer balance).

Founder decisions captured this session (verbatim intent):
- Rail items: Overview, Profile, Saved, Workspace — each of Profile/Saved/Workspace is
  a clickable group that expands a dropdown of its sub-items.
- Strategy is a Profile sub-tab (in the dropdown), developed into a real feature.
- Strategy = job 1 (living doc) **and** job 2 (application game-plan, as a sub-section
  of job 1); job 3 (guided builder) is deferred to a future Uni skill (hook only).
- Rename rail "Home" → **Overview**; rename Profile's "Overview" tab → **Summary**.

## Ship A — rail tree + Messages tab

### Rail (desktop, `MySpaceShell.tsx`)
Expandable tree. Top-level entries:

| Entry | Kind | Target / children |
|---|---|---|
| Overview | link | `/s/space` (today's "Home", renamed) |
| Profile ▾ | group | `/s/profile?tab=` → Summary · Identity · Academics · Experience · Goals · Needs · Strategy · Preferences · Timeline · Analytics · Data |
| Saved ▾ | group | `/s/saved?tab=` → Programs · Schools · Searches |
| Workspace ▾ | group | Prep `/s/prep` · Applications `/s/applications` · Calendar `/s/calendar` |

Behaviour:
- Clicking a group header navigates to its landing view (no `?tab` = first child) **and**
  expands it. A chevron toggles expand/collapse independently.
- The group containing the current route auto-expands on mount; others start collapsed.
  (Local component state seeded from the active route; not persisted — keep it simple.)
- Sub-items are `NavLink`s; active sub-item is highlighted by exact `?tab` match
  (Programs/Summary = the no-`?tab` landing).
- `MY_SPACE_ROUTES` (active-state source for the top nav) drops `/s/messages`.

### Messages → top nav (`StudentLayout.tsx`)
- `NAV_ITEMS`: Uni · Discover · **Messages** (`/s/messages`) · My Space.
- On `/s/messages`, the Messages tab is active and My Space is not (Messages is no longer
  in `MY_SPACE_ROUTES`, and `isMySpacePath` already excludes it).
- The standalone top-right `MessagesNavButton` icon is removed — the nav tab carries the
  unread badge instead (same `getThreads` unread count, cobalt). Mobile bottom bar adds
  Messages.

### Renames
- Rail "Home" label → "Overview" (route unchanged, `/s/space`).
- `ProfilePage` TABS: the `overview` entry's **label** → "Summary" (key stays `overview`,
  so `PROFILE_TABS_SPEC`, redirects, `normalizeProfileTab`, and tests are untouched).
- `StudentTitle` ROUTE_TITLES: `/s/space` title stays "My Space"; no functional change.

### Mobile
Mobile keeps the existing flat horizontal pill row (no nesting): Overview · Profile ·
Saved · Prep · Applications · Calendar. Messages is reachable from the nav (bottom bar /
top), not the pills. The expandable tree is desktop-only.

### Tests
`information-architecture.test.ts` already asserts the room contract; update any
assertion that referenced Messages-in-rail. Add a render test for the rail tree
(groups expand, sub-items deep-link). No redirect changes (all room URLs unchanged).

## Ship B — Strategy living doc (`profile/StrategyTab.tsx`)

Backend is reused as-is — **no migration, no new endpoints**. Existing
`/students/me/strategy` endpoints: `generate`, `active`, `versions`, `{id}`,
`{id}/activate`, `PATCH {id}` (clone-and-modify; already accepts
`academic_path` / `financial_path` / `geographic_path` arrays).

### Section 1 — Your strategy (the living doc)
- Header: career target → target degree, status chip (active / draft), version chip,
  `AIBadge` (stub vs LLM).
- **Editable narrative** + **three editable path tracks**: Academic steps, Financial
  items, Geographic items. The current `NarrativeEditor` only edits career/degree/
  narrative; extend the editor (or add per-track editors) to patch the path arrays too.
  Saving creates a new draft (existing behaviour); an **Activate** action promotes it.
- **Version history**: list versions (`listStrategyVersions`); each row shows status +
  date with **Activate** / view. "Store" = the version trail.
- **Regenerate with AI** (`generateStrategy`) — existing StrategyAgent.
- **Develop with Uni** button — the job-3 hook. Deep-links to `/s` (Uni) with a
  `?intent=strategy` query for now; the guided builder is a future Uni skill, not built
  here. The button is always present so the entry point is discoverable.
- Empty state: generate CTA (needs ≥1 active academic goal upstream — existing
  constraint; surface the reason inline).

### Section 2 — Application game-plan (sub-section of the strategy)
Computed client-side; no new backend.
- **Reach / Target / Safer** balance across saved + applied programs. Reuse the existing
  classification: applications carry `fit_band` (low→reach, medium→target, high→safer),
  the same mapping `ApplicationsPage` already uses for its priority filter. Saved
  programs without an application contribute via their match/fit when available.
- **Portfolio snapshot**: count per band + a gap nudge ("0 safer schools — consider
  adding one to balance your list").
- **What's next**: the 2–3 nearest application deadlines (from the applications list),
  linking into Applications / Calendar.
- Links: "Balance your list" → `/s/saved`, "Your portfolio" → `/s/applications`.

### Tests
Frontend: extend/refresh `StrategyTab` coverage if present (path-edit round-trip,
game-plan banding from a mocked applications list). Backend unchanged → existing
strategy tests remain the gate.

## Out of scope (parked)
- Guided strategy builder (job 3) — future Uni skill; only the hook ships now.
- Server-persisted application game-plan — computed client-side for now.
- Any rail-state persistence across sessions.

## Deployment
Two ships, each: tsc 0 · build 0 · vitest green · preview-verified → merge `main` →
auto-deploy → confirm live (bundle grep + app walkthrough), per the standing rule.
Ship A first (ready, low-risk), then Ship B off updated main.
