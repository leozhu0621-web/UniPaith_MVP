# Discover + Connect merge — hub with a live rail

**Date:** 2026-06-12
**Status:** Approved (user-selected approach A; v1 scope = merge + 6 integration ideas)
**Benchmarks:** LinkedIn home feed / company follow; Handshake employer events + jobs

## Problem

Discover (`/s/explore`, the Match/browse grid) and Connect (`/s/posts`, the
Updates/Events/Peers feed) are fragmented: they surface the same entities
(institutions and programs) through two top-level tabs that never reference
each other. The feed has no distribution — students browsing matches never see
updates from the schools they follow, and the follow graph only grows through
save/apply side effects.

## Decision

Merge Connect into Discover. `/s/explore` becomes a hub with sub-tabs and a
persistent right rail (the "LinkedIn home" model — option A of three presented;
pure tab absorption and a fully interleaved ranked feed were rejected, the
latter because it would bury the structured match experience the product is
built around). Uni (`/s`) is untouched.

## 1. IA & routing

- Student nav drops to three tabs: **Uni · Discover · My Space** (plus avatar).
  Remove the Connectors item from `NAV_ITEMS` in
  `components/layout/StudentLayout.tsx` (desktop nav and mobile tab bar).
- `/s/explore` stays the canonical URL and gains a `tab` query param:
  `foryou` (default, no param) · `updates` · `events` · `peers`.
- `/s/posts` is RETIRED. A `PostsRedirect` element in `App.tsx` maps one-hop:
  - `/s/posts` → `/s/explore?tab=updates`
  - `/s/posts?tab=updates` → `/s/explore?tab=updates`
  - `/s/posts?tab=events` → `/s/explore?tab=events`
  - `/s/posts?tab=peers` → `/s/explore?tab=peers`
- The mapping contract lives as `POSTS_TAB_REDIRECTS` in
  `utils/information-architecture.ts`, tested in
  `test/information-architecture.test.ts` (same pattern as
  `MANAGE_TAB_REDIRECTS` for the retired `/s/manage`).

## 2. Discover hub layout

### Sub-tab bar

Under the `PageHeader` (eyebrow "Discover"), an ARIA tablist (reuse the
keyboard-navigable pattern from the deleted `PostsPage`): **For you ·
Updates · Events · Peers**. Tab selection syncs to the `tab` URL param.
Updates and Events tabs show a small badge with the count of items new since
last visit (see §6 badges).

### For you tab (default)

Keeps today's Explore scroll untouched in the main column: StrategyView →
featured promotions → MatchesSection (banded) → DiscoverySearch → browse
universities. At `xl+` the tab becomes a two-column grid: main column +
sticky right rail (~`w-80`). The page stays full-bleed (`w-full`) per the
app-shell rule — the rail adds density, it does not shrink content into a
centered column. The rail stays visible while `searchActive` (it is ambient
context, not search UI). Below `xl` the rail is hidden; its signal survives
as the tab badges.

### Right rail (xl+), four compact cards

1. **From your schools** — latest 3 items from `GET /connect/feed` (compact
   rows: institution, title, relative time). Reuses the "new since last
   visit" pill logic (localStorage key `unipaith_connect_last_seen`).
   "See all" → Updates tab. Rail rows fire NO view-engagement events (avoid
   skewing per-post tracking); clicking a row opens the Updates tab.
2. **Upcoming events** — next 2–3 from `GET /connect/events?scope=upcoming`,
   date chip + RSVP state. "See all" → Events tab.
3. **Deadline radar** — the 3 soonest deadline items via
   `GET /connect/feed?kinds=deadline` (new param, §5).
4. **Following** — followed-school count + "Manage" link opening the existing
   `ManageFollowingPanel` sheet; plus **follow suggestions** (§6).

## 3. Updates / Events / Peers tabs

`UpdatesTab`, `EventsTab`, `PeersTab`, and `ManageFollowingPanel` move into
the Explore shell unchanged (files stay in `pages/student/connect/`).
`PostsPage.tsx` is deleted. Peers keeps its existing flag/opt-in gating.
Infinite scroll, rank toggle, RSVP, and the cursor pill all behave exactly as
today.

## 4. Naming

Nav label stays "Discover". PageHeader title varies by tab: For you keeps
"Your strategy and your matches"; Updates/Events/Peers reuse their existing
titles as the subtitle line.

## 5. Backend changes (all in `connect.py` router + `connect_service.py`)

1. **`kinds` filter on `GET /connect/feed`** — optional comma-list
   (`post,deadline,program_change,saved_search_alert`); filters at assembly.
2. **`follow_source` on feed items** — the existing follow row's `source`
   (`saved | application | explicit`) joined into each feed item so the
   frontend can render attribution (§6).
3. **`GET /connect/unseen-count?since=<iso>`** — cheap COUNT of feed items
   newer than `since` for the nav badge; no item assembly.
4. **Saved-search alert feed items** — `build_updates_feed` appends
   `kind='saved_search_alert'` items derived from the student's
   `saved_searches` where `alert_enabled` and `last_alerted_at` is within 14
   days and `last_match_count > 0`: title `"N new programs match '<name>'"`,
   CTA deep-links to `/s/explore` with the saved query restored (existing
   run-saved-search flow). No new table; derived at read time.

The flag-fallback invariant holds: none of these touch AI paths; all are
deterministic.

## 6. v1 integration ideas (shipping with the merge)

| # | Idea | Benchmark | Mechanics |
|---|------|-----------|-----------|
| 1 | **Follow button on cards** | LinkedIn company follow | `UniversityCard` and `ProgramCard` get a follow/following toggle (follows are institution-level; on ProgramCard it follows the program's institution). Uses existing `POST/DELETE /connect/follows/{id}`; followed-ids set comes from the existing `GET /connect/follows` query on the page. |
| 2 | **"Because you follow X" attribution** | LinkedIn feed attribution | Feed cards render a muted caption from `follow_source`: "Following · saved program", "Following · application", "You follow this school". |
| 3 | **Badge counts** | LinkedIn notification dots | Updates/Events sub-tab badges (new-since-last-visit, localStorage compare) + a dot on the Discover nav item via `GET /connect/unseen-count` (lightweight query in StudentLayout, 5-min staleTime, student role only). |
| 4 | **Event chips on cards** | Handshake employer events on job cards | Client-side join: the page's upcoming-events query builds `institution_id → next event` map; `MatchCard`/`ProgramCard` render an "Info session Thu" chip when their institution has one. No backend change. |
| 5 | **Saved-search alerts in feed** | LinkedIn job alerts in feed | §5.4 feed items, rendered as a distinct card with a "Run search" CTA. |
| 6 | **Follow suggestions in rail** | LinkedIn "Add to your feed" | Client-side: institutions from top matches + saved programs not yet followed, top 3 by fitness; one-tap Follow via existing endpoint. |

## 7. Backlog (NOT v1)

- **Peer signals on cards** ("4 peers are also looking") — needs backend
  aggregation + privacy gating beyond the peer opt-in; high cost.
- Interleaved ranked home feed (option C) — revisit only if rail engagement
  proves demand.
- Follow toggle on `MatchCard` (kept off v1 to protect card density).

## 8. Testing

- **Frontend:** extend `information-architecture.test.ts` with
  `POSTS_TAB_REDIRECTS` (every legacy URL maps one-hop, no dead tabs); render
  tests for the hub (tab switching syncs URL; rail hidden below xl is CSS so
  smoke-test presence at default); follow-toggle optimistic update; badge
  computation pure-function test.
- **Backend:** `kinds` filtering, `follow_source` presence, unseen-count
  correctness, saved-search alert item assembly (alert_enabled off → absent;
  stale `last_alerted_at` → absent) — added to the existing connect test
  files.
- Full suites green before merge (standing rule), then deploy + verify live
  by grepping the production bundle for a new marker string.

## 9. Cleanup

- Delete `PostsPage.tsx`; route element replaced by `PostsRedirect`.
- `NAV_ITEMS` 4 → 3; mobile tab bar follows automatically.
- No model/migration changes; no AI-flag changes.
