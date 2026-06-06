# Student-side UI densification — design

**Date:** 2026-06-04
**Status:** approved (brainstorming) → implementation

## Goal

Shift the student app's overall feel toward a denser, more utilitarian, **LinkedIn-like
"app" feel**, applied systematically across all ~17 student surfaces as a *detail pass* —
**without re-architecting any surface's layout**. Reversible, low-collision, token-faithful.

## Non-goals

- No layout re-architecture (no new rails, no 3-column app shell).
- No new decorative imagery/gradients/marketing flourish — *density is not decoration*; that
  rule stays.
- Not the parallel session's lane: design-token unification, skeleton/loading/error states,
  keyboard-a11y. This effort **uses** their tokens and stays off those files.

## The densification rubric (detail rules, applied everywhere)

1. **Tighten vertical rhythm** — cut section gaps ~30–40%; page headers go from
   magazine-scale to compact app-scale.
2. **Denser list rows** — compact rows (hairline divider + hover) instead of tall bordered
   pills; ~50% more rows visible per screen.
3. **Surface metadata + counts/badges** — progress meters, per-section counts, inline stats
   where LinkedIn shows them.
4. **Utilitarian section headers** — small eyebrow label + count, not big editorial heads.
5. **Kill dead whitespace** — fill empty columns with useful density.
6. **One consistent app chrome** — every surface shares the same compact `PageHeader`,
   dense `ListRow`, and `StatTile`.

## Mechanism

Rules 1–6 are mostly **shared-component changes** — changed once, propagating to all
surfaces. New components in `frontend/src/components/student/density/`:

- **`PageHeader`** — eyebrow + small heading + optional count/right-actions, tight padding.
- **`ListRow`** — short row: optional left media, title + dense subline, trailing slot;
  hairline divider, hover; not a bordered pill.
- **`StatTile`** — compact label + value (+ optional sub), for stat strips.
- **`SectionHeader`** — small uppercase eyebrow + count, the standard section label.

All use the existing semantic tokens (`text-foreground`/`muted-foreground`/`secondary`/
`border`/`muted`) — **no new colors**. Each ships with a vitest render test.

## Rollout (each wave = its own tested + pushed PR, fresh branch off latest `main`)

- **PR 0:** the density layer (the 4 shared components above) + this spec + the `CLAUDE.md`
  update. No surface behavior change yet.
- **Wave A:** Discover (`DiscoverHomePage`), Match (`ExplorePage`), Apply (`ManagementPage`:
  Applications · Calendar · Messages).
- **Wave B:** program detail (`ProgramDetailPage`), school detail (`InstitutionDetailPage` /
  `SchoolSubunitPage`), Profile (`ProfilePage`).
- **Wave C:** Connect (`PostsPage`), Saved (`SavedListPage`), Settings (`SettingsPage`),
  Recommendations, Financial Aid, Onboarding, Interviews.

Per surface: swap to the dense components → kill dead whitespace → surface metadata →
tighten rhythm. Then **screenshot it live** and verify density up, nothing broken.

## Docs

Update `CLAUDE.md` "UI/Design Preferences": editorial-restraint/whitespace →
dense/utilitarian/app-like (LinkedIn-leaning) *within existing layouts*; **keep** "no
decorative images/gradients/color accents".

## Coordination

Parallel session owns tokens/states/a11y; this owns density components + per-surface layout.
Sequence to avoid hot-file collisions; use **fresh-branch-off-latest-`main` per PR** (the
squash-divergence-safe pattern). Leave a note in the shared memory.

## Validation (per PR)

- Live screenshot of each touched surface (density improved, nothing broken).
- `tsc -b` + `eslint` + `vitest` green before push.

## Success criteria

- Every student surface visibly denser + more app-like, using the same shared chrome.
- No layout breakage; no token/state/a11y regressions; all tests green.
- `CLAUDE.md` reflects the new design law.
