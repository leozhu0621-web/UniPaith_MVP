# My Space rail restructure — group rooms by content type, not journey phase

**Date:** 2026-06-14
**Status:** Approved (user-selected: Option 2 — group by content type; noun labels; order Record → Collections → Workspace)

## Problem

The My Space room rail (`MySpaceShell.tsx`) groups rooms by the **phases of a
single application's lifecycle**: `Plan → Prepare → Apply & decide → Anytime →
Record`. The user finds this confusing — it reads as "the sequence of one
submission" rather than a logical, durable structure. Because almost every
group holds exactly one room, the phase **labels** carry the entire timeline
feeling.

## Decision

Regroup the rail by **what each room holds** (a logical, database-like
taxonomy) using neutral noun category labels, identity-first:

```
Home                  ← ungrouped, on top (the dashboard)

RECORD
  Profile             ← your durable reference data

COLLECTIONS
  Saved               ← programs you're tracking
  Applications        ← your submissions

WORKSPACE
  Prep                ← your materials (essays, interviews, recommenders, prompts)
  Calendar            ← your schedule
  Messages            ← your conversations
```

The taxonomy reads identity → tracked objects → where you act, with no phase
words anywhere.

## Scope

This is a **presentational change to one file** (`MySpaceShell.tsx`):

- **`GROUPS` array** — relabel + reorder to `Record (Profile) → Collections
  (Saved, Applications) → Workspace (Prep, Calendar, Messages)`. Home stays the
  ungrouped first entry.
- **Room coachmark copy** (`id="myspace-rooms"`) — replace the journey framing
  *"Rooms, in journey order / Plan, prepare, apply and decide — the rail
  follows your journey top to bottom…"* with content-type framing, e.g.
  *"Your rooms, organized / Grouped by what's inside — your record, your
  collections, and your workspace. Home pulls it all together."*
- **File header comment** — update the "journey sequence" description.

## What does NOT change

- **Rooms and routes** — same 7 rooms, same flat URLs (`/s/saved`, `/s/prep`,
  `/s/applications`, `/s/calendar`, `/s/messages`, `/s/profile`, `/s/space`).
- **`MY_SPACE_ROUTES`** — still derived from `ALL_ROOMS`; identical set, so
  `StudentLayout`'s My-Space active-state logic is unaffected.
- **Badges** — Messages unread pill + Applications count carry over unchanged
  (keyed by `to`, not by group).
- **Mobile pill row** — still renders `ALL_ROOMS` flat; the new flat order
  becomes `Home · Profile · Saved · Applications · Prep · Calendar · Messages`.
- **No IA contract change** (`information-architecture.ts` /
  `MANAGE_TAB_REDIRECTS` / `POSTS_TAB_REDIRECTS` untouched); no routes added or
  removed.

## Architecture

`MySpaceShell.tsx` already renders `GROUPS` generically (a `.map` over
`{ label, rooms }` with an eyebrow label per non-null group, and `ALL_ROOMS =
GROUPS.flatMap(g => g.rooms)` driving the mobile pills and `MY_SPACE_ROUTES`).
Only the **data** in `GROUPS` changes; the rendering, badges, active-state, and
route-export code are untouched. This keeps the unit boundary clean: the rail's
*organization* is data, its *rendering* is the component.

## Testing

A new `frontend/src/test/myspace-shell.test.tsx`:
- Renders `MySpaceShell` (in `MemoryRouter` + `QueryClientProvider`, mocking
  `getThreads` / `listMyApplications`) and asserts:
  - the three category labels `Record`, `Collections`, `Workspace` are present,
    and the journey labels (`Plan`, `Prepare`, `Apply & decide`, `Anytime`) are
    absent;
  - all 7 room links are present with their correct `href`s (routes unchanged);
  - the rail order is `Home, Profile, Saved, Applications, Prep, Calendar,
    Messages` (assert the rendered nav link order).

`tsc -p tsconfig.app.json --noEmit` + `npm run build` + full `vitest` green.

## Visual verification + ship

Live preview: confirm the desktop rail shows the new groups/labels in order and
the mobile pill row follows the new flat order; badges still appear. Then ship
to production and verify the live `MySpaceShell` chunk contains `Collections` /
`Workspace` and no `Apply & decide`.

## Cleanup

None — single-file edit plus one new test. No deletions, no migrations.
