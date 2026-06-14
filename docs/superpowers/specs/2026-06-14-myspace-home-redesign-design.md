# My Space home redesign — focus · momentum · density

**Date:** 2026-06-14
**Status:** Approved (user-selected: synthesize all three directions; v1 modules = readiness hero + journey map, this-week ribbon, strategy snapshot + smart empties)
**Benchmarks:** Imprint (progress viz, springy reveal, celebration), LinkedIn ("your week" recap), Handshake (stage track), Notion/Linear (dense organized modules)

## Problem

The My Space home (`/s/space`, `MySpaceHomePage.tsx`) is mission-control-correct but
emotionally flat: monochrome gray ListRows on cream, plain number tiles with no
animation, and — for any student without a busy pipeline — half the panes render
barren empty strings ("Nothing urgent", "No outstanding requests", "No workshop runs
yet"). The one inspiring element, the gold journey ring (`JourneyChecklistCard`),
*self-hides at 100%* so established students see nothing motivating. A pile of
motivating, already-fetchable data (journey stage, weekly activity, strategy) never
appears.

## Decision

Redesign the home as a top-to-bottom synthesis of three product POVs the user picked
together:

- **C (focus)** — a single "Today's focus" focal point at the very top.
- **A (momentum)** — an inspiration band: progress ring + journey-stage map + this-week ribbon.
- **B (density)** — the existing dense mission-control dashboard below.

**Zero backend changes.** Every module is client-side composition of existing
endpoints (consistent with the original My Space spec's "Home = client-side
composition" principle). All data shapes were verified to exist on real, timestamped
fields (see §7).

## Layout (top to bottom)

1. **Greeting** — keep the existing time-based greeting + first name, wrapped in the
   `myspace-home` Coachmark + `PageHeader`. Unchanged.
2. **Today's focus** (new — `home/TodaysFocus.tsx`)
3. **Momentum band** (new — `home/MomentumBand.tsx`, composing `JourneyMap` + `WeekRibbon`
   + the folded-in onboarding ring)
4. **Pipeline** stat strip — existing, upgraded with count-ups + earned-gold Offers tile
5. **Up next** — existing, minus the action promoted into Today's focus
6. **Deadlines | Waiting on others + Latest feedback** — existing, with smart empty states
7. **Strategy snapshot** (new — `home/StrategySnapshot.tsx`)
8. Quiet footer link — existing

## Modules

### 1. Today's focus (`home/TodaysFocus.tsx`)

The single highest-priority action, large and prominent — "one focal point per view"
(Imprint). Reuses the existing `upNext` priority computation from `MySpaceHomePage`
(order: overdue deadline › pending offer › interview slots › top-readiness draft ›
clarifications). `TodaysFocus` renders `upNext[0]`; the **Up next** section renders
`upNext.slice(1)`.

- Renders: an accent icon, the action title, its context sub-line, urgency chip, and a
  primary CTA button navigating to the action's `to`.
- **Caught-up state** (upNext empty): a positive card — "You're all caught up" + one
  suggested next move (if onboarding < 100% → "Keep building your profile" → the next
  onboarding step's route; else → "Talk to Uni" → `/s`). Never a dead string.
- Visual: a `Card pad={false} p-5` with a left accent matching urgency
  (error/warning/secondary). Gold is NOT used here (routine, not earned).

To keep the priority logic single-sourced, extract the current inline `upNext` builder
into `home/upNext.ts` exporting `buildUpNext(inputs): NextAction[]`; both
`MySpaceHomePage` (for the list) and the page's `TodaysFocus` render consume the one
array.

### 2. Momentum band (`home/MomentumBand.tsx`)

One card holding three sub-parts. The band always renders (even for established
students); only the ring + setup steps self-hide at 100%.

**a. Onboarding ring (folded in from JourneyChecklistCard)**
- Source: `getOnboarding()` → `OnboardingStatus.completion_percentage` (the exact source
  the current `JourneyChecklistCard` uses — so there is ONE percentage on the page, not
  two competing ones).
- Reuse the existing `ProgressRing` (gold ring, double-rAF initial fill, `useCountUp`
  numeral) — move it from `JourneyChecklistCard.tsx` into `home/ProgressRing.tsx` and
  import it in both places, OR keep `JourneyChecklistCard` as the owner and render the
  ring + next-3-steps inside the band. **Decision: the MomentumBand renders the ring +
  next-3-steps directly (absorbing `JourneyChecklistCard`'s body), and
  `JourneyChecklistCard.tsx` is deleted** — its responsibility moves into the band so
  the home has one progress surface. The `['onboarding']` query key and the `STEP_SPECS`
  table move into the band unchanged. Self-hide rule: when `completion_percentage >= 100`
  the ring + steps are omitted but the band's journey map + ribbon still render.
- Gold ring fill is the already-shipped "rare gold progress" exception (Ship C) — kept.

**b. Journey-stage map (`home/JourneyMap.tsx`)**
- A horizontal 4-node track: **Discover › Match › Apply › Decide**. Past stages filled,
  current stage lit in **cobalt** (`--secondary`), future stages muted. Chrome/structure
  → cobalt, never gold.
- Current stage derived client-side from data the home already fetches (no new query):
  - `Decide` — any application `status === 'decision_made'` OR `offers.length > 0`
  - `Apply` — any application exists (`appList.length > 0`)
  - `Match` — `saved.length > 0` (saved programs imply matching happened); the home
    already fetches saved. (Matches/strategy are NOT fetched by the home today; do not
    add a query for v1 — `saved` is a sufficient, already-present Match signal.)
  - `Discover` — default earliest stage otherwise.
  - Pick the furthest-reached stage as "current".
- Each node is a button deep-linking to that stage's surface (`Discover`→`/s`,
  `Match`→`/s/explore`, `Apply`→`/s/applications`, `Decide`→`/s/applications?tab=offers`).

**c. This-week ribbon (`home/WeekRibbon.tsx`)**
- Counts only items with real timestamps in the last 7 days:
  - saved this week — `SavedProgram.added_at`
  - essays/feedback this week — `WorkshopFeedbackRun.created_at`
  - submitted this week — `Application.submitted_at`
  - (profile/goal additions are NOT counted in v1 — the home doesn't fetch goals; keep to
    the three already-fetched sources.)
- Render: "This week · +2 saved · 1 reviewed · 1 submitted" — only non-zero segments
  shown, joined by `·`.
- **Smart empty** (all zero): "A quiet week so far — pick one thing below to move
  forward." Never a dead string.
- Counting is pure (a `countThisWeek(inputs)` helper) and reduced-motion-agnostic.

### 3. Pipeline strip (existing, upgraded)

- Wrap each `StatTile` value in `useCountUp` so the four numbers count up on mount
  (`useCountUp` already gates reduced-motion → instant).
- **Earned-gold Offers tile**: when `offers.length > 0`, the Offers tile gets a gold
  treatment (gold value text + a faint gold ring), the page's single routine gold accent
  tied to a real achievement. All other tiles stay cobalt/neutral. When `offers.length
  === 0` the Offers tile is plain neutral.

### 4. Strategy snapshot (`home/StrategySnapshot.tsx`)

- Source: `getActiveStrategy()` → `StudentStrategy | null`. New query
  `['strategy','active']` on the home (shared key with `StrategyView`, so cache is reused
  when navigating to `/s/explore`).
- Active strategy: a compact card — `career_target` → `target_degree` as the headline
  (skip nulls gracefully), a 2-line clamp of `narrative` if present, and a "Refine" link
  → `/s/explore?showStrategy=open` (the existing deep link `StrategyView` reads).
- Null strategy (or `is_stub`): smart empty — "Shape your path with Uni" → `/s`.
- Placement: full-width module between the two-column row and the footer (its own row).

### 5. Smart empty states (existing panes)

Replace barren strings with encouraging next-move prompts + a CTA:
- **Deadlines** empty → "Nothing due in the next two weeks — a good time to get ahead in
  Prep." + `Prep →`.
- **Waiting on others** empty → "No pending requests. When you ask for a recommendation
  it'll show here." + `Request a letter →` (`/s/prep?tab=recommenders`).
- **Latest feedback** empty → keep the existing helpful copy (already a prompt).
- **Up next** empty is handled by Today's focus's caught-up state; the Up next section
  hides entirely when `upNext.slice(1)` is empty.

### 6. Earned-gold win beat

- When a *fresh* win is present — a new offer id not seen before, or an application whose
  `submitted_at` is within the last 7 days and not previously celebrated — fire exactly
  one `.animate-beat` gold pulse on the Offers tile (or the submitted app's pipeline
  context).
- Freshness tracked via a localStorage marker `myspace_celebrated` storing the set of
  celebrated win ids; a win beats once, ever. Reduced-motion → no beat (the `.animate-beat`
  CSS is already gated).

## Motion

- Page root stays `PageContainer` (carries the page entrance + full-bleed container).
- The module sequence keeps the `stagger-list` cascade (the pronounced #511 values:
  16px+scale travel, ~520ms, `--ease-entrance`, 70ms step) — new modules slot into the
  existing `stagger-list` wrapper so they cascade with the rest.
- Count-ups: pipeline stats + onboarding ring numeral (existing `useCountUp`).
- One gold beat on a fresh win (above).
- Everything under both reduced-motion gates (`prefers-reduced-motion` +
  `html[data-reduce-motion]`); JS-timer animations (`useCountUp`) already gate via
  `prefersReducedMotion()`.

## Constraints respected

- **Full-bleed app-shell** — `w-full`, no `max-w` cap (`PageContainer` already enforces).
- **Gold = earned only** — used solely on the onboarding ring (shipped exception), the
  Offers tile when offers exist, and the one-shot win beat. Journey map + all chrome =
  cobalt. No gold on structure.
- **Density layer** — new modules use `Card`, `SectionHeader`, `ListRow`, `StatTile`.
- **IA contract** — no route/nav changes; `information-architecture.ts` untouched.
- **Zero backend** — only the one new client query (`getActiveStrategy`) is added; all
  else reuses queries the home already runs.

## File structure

```
pages/student/myspace/
  MySpaceHomePage.tsx        # slimmed to a composition: greeting + <TodaysFocus> +
                             # <MomentumBand> + pipeline + Up next + two-col + <StrategySnapshot>
  JourneyChecklistCard.tsx   # DELETED — body absorbed into MomentumBand
  home/
    upNext.ts                # buildUpNext(inputs) — extracted priority logic + NextAction type
    TodaysFocus.tsx          # the #1 action / caught-up hero (C)
    MomentumBand.tsx         # ring + JourneyMap + WeekRibbon (A)
    ProgressRing.tsx         # moved out of JourneyChecklistCard, reused by MomentumBand
    JourneyMap.tsx           # Discover › Match › Apply › Decide track
    WeekRibbon.tsx           # this-week activity recap + smart empty
    StrategySnapshot.tsx     # strategy one-liner / smart empty
    celebrate.ts             # localStorage win-id tracking for the gold beat
    weekActivity.ts          # countThisWeek(inputs) pure helper
```

Each file has one clear responsibility and is independently testable. `MySpaceHomePage`
becomes a readable top-level composition instead of one ~370-line file.

## Testing

Frontend (`vitest` + `@testing-library/react`, `MemoryRouter` wrapper):
- `upNext.ts` — `buildUpNext` priority order + max-5 cap (pure unit).
- `weekActivity.ts` — `countThisWeek` counts only last-7-day timestamps; all-zero path.
- `JourneyMap` — derives the correct current stage from each signal combination
  (Discover/Match/Apply/Decide), furthest-reached wins.
- `TodaysFocus` — renders `upNext[0]`; caught-up state when empty.
- `StrategySnapshot` — active vs null/stub rendering.
- `celebrate.ts` — a win id beats once, then never again (localStorage marker).
- `MySpaceHomePage` smoke — renders all modules with mocked queries without crashing;
  brand-new empty state still renders.
- Full `vitest` + `tsc -p tsconfig.app.json --noEmit` + `npm run build` green before merge.

## Visual verification

Live local preview (isolated seed DB) covering: a sparse student (most panes
smart-empty, journey at Discover/Match, ring visible) and a busy student (offers →
gold tile + win beat, journey at Decide, ribbon populated, ring hidden at 100%).
Desktop + mobile + dark mode + reduced-motion. Then ship to production and verify the
live bundle.

## Cleanup

- Delete `JourneyChecklistCard.tsx` (body moved into `MomentumBand`); update its sole
  importer (`MySpaceHomePage`).
- No migrations, no AI-flag changes, no IA changes.
