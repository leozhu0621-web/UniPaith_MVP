# Platform UX overhaul — motion, layout, friendliness, onboarding

**Date:** 2026-06-12 · **Status:** Approved (founder direction: "overall optimization of UX for the entire platform… lots of animation, better layout and sizing… more user friendly… full scale onboarding — plan first, then implement") · **Design reference:** **Imprint** (the visual-learning app) for UX, visualization, and animation — adapted to web/desktop, layered onto (not replacing) UniPaith's cream/cobalt/gold editorial identity and the dense LinkedIn-leaning utility surfaces.

Grounding: 5-auditor + critic workflow run `wf_5a846e37-947` (2026-06-12) over `frontend/src`; findings cited inline as `file:line`.

## Problem

Four compounding gaps:

1. **Layout/sizing bugs** — the founder's screenshot of the Discover hub (clipped "Talk to Uni" card, rail cut off, empty top band) is one panned wide page: `StudentLayout`'s `<main>` only sets `overflow-y-auto`, so overflow-x computes to `auto` and any too-wide child horizontally pans the whole shell (`StudentLayout.tsx:165`); `ScrollReset` never clears `scrollLeft` so the pan persists across routes (`ScrollReset.tsx:14`); the live rail is a fixed `19rem` track gated by px breakpoints that desync from rem font-scaling (`ExplorePage.tsx:286`, `index.css:264-267`); `Card` has no default padding so hub cards render flush to the border (`Card.tsx:16-21`). Plus 5 different page-padding recipes, a tablist that breaks at 360px (`PrepPage.tsx:74`), a `max-w-4xl` full-bleed violation (`WorkshopsTab.tsx:67`), and grids that stop densifying at `lg:grid-cols-3`.
2. **Motion system built but unadopted** — Spec 77 tokens/keyframes exist but `stagger-list` is used in 2 files, `--ease/--dur` are referenced 0 times from TSX, all overlays are enter-only with no exit animation, tab changes hard-swap, content hard-pops after loading, rings/stats render pre-filled/static. No JS animation dep (good — keep CSS-only).
3. **Friction** — scroll position destroyed on back-navigation (the one **critical** finding, `ScrollReset.tsx:11`), div-onClick cards with no keyboard/link semantics, silent mutation failures (program save, RSVP, mute/unfollow), `['saved']` vs `['saved-programs']` cache split-brain, profile edits and 20k-char workshop drafts silently destroyed on tab switch, dead-end empty states.
4. **Onboarding is a stub** — a skippable 3-step wizard reachable via email signup or a fragile 60-second account-age heuristic after OAuth (`AuthCallbackPage.tsx:42`); abandonment is unrecoverable; the backend's 13-step `onboarding_progress` engine and the typed `lib/analytics.ts` funnel bus both have ~zero consumers; only 3 coachmarks exist app-wide.

Two prerequisites no surface-level fix can dodge: **App.tsx has 82 eager page imports and zero route-level code splitting** (first paint gates the onboarding moment), and **funnel instrumentation is dead** (an onboarding overhaul would be unmeasurable).

## Decisions

- **Imprint as motion/visualization north star**: one focal point per view; springy ease-out entrances; sequential reveal over hard pops; segmented progress bars + animate-fill rings; celebration beats in earned-gold; onboarding = one question per screen with big tappable option cards.
- **CSS-only motion** — no framer-motion; extend the Spec 77 token system and route everything (including tailwind.config keyframes) through `--ease/--dur` tokens. All new motion sits under both existing reduced-motion gates.
- **One scroll/navigation policy** (resolves the 3-way auditor conflict): restore scroll on POP (per `location.key`, sessionStorage), reset on PUSH — including `?tab=` changes — and always clear `scrollLeft`. Page-entrance animation moves inward (PageContainer / shell content column), so shells stop remounting per room/tab change.
- **Container hygiene over container queries (v1)**: fix overflow with `overflow-x-clip` + `min-w-0` + `break-words` + softened `minmax(0,19rem)` rail track; no new Tailwind plugin this round (follow-up note §7).
- **Onboarding is server-persisted** — a small migration (`student_profiles.onboarding_state JSONB`) replaces the 60-second heuristic; abandoning resumes on next login. The wizard hands off to Uni; My Space home gets the journey checklist fed by the existing 13-step engine.

## 1. Ship A — Foundations & layout (the screenshot bug class)

**Shell containment & scroll policy**
- `StudentLayout.tsx:165` `<main>`: add `overflow-x-clip min-w-0`; root `h-screen` → `h-dvh` (`:70`).
- Rewrite `ScrollReset.tsx`: sessionStorage scroll map keyed by `location.key`; restore on POP, reset on PUSH/REPLACE (watch `pathname + search`), always `main.scrollTo({left: 0, ...})`.
- Remove the pathname key from the `Outlet` wrapper (`StudentLayout.tsx:168-171`); entrance animation moves into `PageContainer` (below). MySpaceShell rail and hub tab bars stop being remounted/scrolled away.

**Container standardization**
- New `components/student/density/PageContainer.tsx`: the single page recipe — `w-full px-4 sm:px-6 py-5` (+ `pb-24 md:pb-8` where the mobile tab bar needs clearance), and it carries the page-entrance animation class. Adopt on all app-shell student surfaces (Explore hub, My Space home + rooms, Applications, Calendar, Saved, Profile, Settings, Messages, Feedback inbox). Detail pages keep `max-w-5xl mx-auto` per standing rule.
- `Card.tsx`: default `p-5` via a `pad` prop (default on); mechanical sweep — call sites already passing `p-*` in className get `pad={false}`. Kills the flush "Talk to Uni" card (`StrategyView.tsx:110`).
- Discover rail: track → `xl:grid-cols-[minmax(0,1fr)_minmax(0,19rem)]`; `min-w-0` on grid children + `break-words` on card titles (`MatchesSection.tsx:216,223`, `ExplorePage.tsx:298,390`); sticky rail gets `max-h-[calc(100dvh-…)] overflow-y-auto`.
- `PrepPage.tsx:74` tablist `overflow-x-auto`; `WorkshopsTab.tsx:67` drop `max-w-4xl`; PageHeader adoption on Profile/Settings/FeedbackInbox; grids gain `xl:grid-cols-4` where cards are compact (per CLAUDE.md density rule) with the `min-w-0` guards making font-scaling safe.
- Toast stack offset above the mobile bottom tab bar (`Toast.tsx:32`); My Space mobile pill row sticky (`MySpaceShell.tsx:104`).

**Performance prerequisite**
- Route-level code splitting in `App.tsx`: `React.lazy` per page (82 eager imports today), router-level `<Suspense fallback={<PageLoader/>}>`. Auth/layout/redirect components stay eager.
- Hub-top placeholders switch from blank `animate-pulse` rectangles to `up-skeleton` shimmer with content-shaped bars (`StrategyView.tsx:91`, `MatchesSection.tsx:138-141`, `ExplorePage.tsx:362-364`).

## 2. Ship B — Motion layer (Imprint language, CSS-only)

**Token unification** (`index.css` + `tailwind.config.js`)
- New tokens: `--ease-spring: cubic-bezier(0.34, 1.3, 0.64, 1)` (gentle overshoot for selections/celebrations), `--dur-page: 280ms`.
- tailwind.config keyframe easings/durations re-pointed at the CSS tokens (one vocabulary). `animate-page-in` retired in favor of `.page-enter` on PageContainer.

**New primitives**
- `.page-enter` — opacity 0→1, translateY 12px→0, `--dur-page` `--ease-out`.
- `.stagger-list` extended to 12 children (40ms steps; n+13 → 0ms).
- `usePresence(open, dur)` hook — `{mounted, closing}` for exit animations; adopted by Modal, Sheet, Dropdown, Popover, Toast, CompareTray (backdrop fade both ways, panel scale/slide out).
- Sliding tab underline in the `Tabs` primitive + `DiscoverTabBar` (transform-based indicator); tab panels get a 160ms fade/rise on key change.
- `useCountUp(value, ~600ms)` (rAF, reduced-motion → instant) for `StatTile` and score numerals.
- `DualRing` ring-fill animates on mount (rAF-triggered dashoffset transition, `DualRing.tsx:118-131`); `ProgressBar` animates initial fill.
- Button press feedback `active:scale-[0.98]` on primary/secondary variants; `hover-lift` adopted on interactive cards (university/program/match).
- Uni chat bubbles entrance (fade/rise per message, `UniConversation.tsx:44-47`).
- Milestone celebration beat: existing `animate-beat` + earned-gold, applied on match-band reveals and onboarding completion; `useMilestoneBeat` hold timer gated by reduced-motion (`useMilestoneBeat.ts:15`).

**Adoption sweep** — `stagger-list` + post-loading fade on every major grid/list: Explore (matches, promos, universities), Updates/Events/Peers, My Space home modules, Applications, Saved, Calendar agenda, Profile tab panels. One skeleton idiom: raw `animate-pulse` blocks on student surfaces → `up-skeleton`.

## 3. Ship C — Full-scale onboarding (Imprint-style)

**Wizard** — rebuild `OnboardingPage.tsx` as a full-screen guided flow: segmented progress bar on top, ONE question per screen, big tappable option cards (icon + label, spring `scale` selected state), slide-left/right step transitions, Enter/keyboard support, skippable per-step but never lost:

1. **Welcome** — greeting + "2 minutes to personalize" + value framing.
2. **Stage** — "Where are you in your journey?" (Just exploring / Building my list / Ready to apply / Deciding offers).
3. **Field of interest** — multi-select chips seeded from the 15-track major catalog.
4. **Degree level** — Bachelor's / Master's / MBA / PhD.
5. **Timeline** — target intake term.
6. **Constraints** (skippable) — budget band + preferred geographies.
7. **"Setting up your space"** — animated build moment (ring fill + staggered checklist of what was personalized) → handoff: **"Talk to Uni"** (primary) / "Explore matches".

**Persistence & entry** — migration adds `student_profiles.onboarding_state JSONB` (answers + `completed_at` + `dismissed_at`); `GET/PATCH` exposed on the existing student profile endpoints (schemas updated same change, per Data & Schema Rules). Answers also fan into existing structures where they map cleanly (field of study → academic record; stage → journey emphasis; goals via `student_goals` source=manual). Routing: post-auth (both email and OAuth) → server flag check → `/onboarding` if incomplete; the dead `onboardingPending` param (`auth-redirect.ts:18`) gets wired; the 60-second heuristic dies. Resume on next login if abandoned.

**Journey checklist** — My Space home `brandNew`/`upNext` slots gain an animated checklist card + progress ring consuming the shelf-ware `GET /students/me/onboarding` 13-step engine (`student_service.py:749`): ring fills on mount, steps stagger in, next-step CTA deep-links.

**Coachmark tour** — extend the existing queue/store to ~7 first-visit marks: Discover tabs, live rail, compare tray (re-triggered where it can actually fire), My Space rooms rail, Uni journey rail, profile strength, saved-search entry.

**Instrumentation** — wire the dead `lib/analytics.ts` funnel bus: `onboarding_started/step_completed/completed/skipped`, checklist clicks, coachmark dismissals. `DemoNotice` becomes once-per-account (localStorage), not once-per-session.

## 4. Ship D — Friendliness (friction fixes)

- **Card link semantics**: University/Program/Promo cards → real `<Link>` (keyboard + cmd-click), inner actions `stopPropagation` (`UniversityCard.tsx:60`).
- **Mutation feedback**: onError toasts + optimistic UI for program save (`ProgramDetailPage.tsx:183`), RSVP (`EventsTab.tsx:49`), mute/unfollow + error-vs-empty in `ManageFollowingPanel.tsx:12`; `RationalePopover` error state with retry (`:87`).
- **Cache unification**: `['saved']` vs `['saved-programs']` → one key via the Spec 54 `queryKeys` module.
- **Stop destroying input**: wire the built-but-unused `useAutosave`/`SaveStatus` into profile tabs (`profile/shared.tsx:350`); workshop essay/interview drafts persist to localStorage keyed per program (`EssayFeedbackPanel.tsx:35`).
- **Empty-state dead-ends**: recommenders stale pointer (`ApplicationDetailPage.tsx:1119`), "Match"→"Discover" copy drift (`SavedListPage.tsx:317`), attachment-picker upload path (`AttachmentPicker.tsx:25`).
- **Affordances**: nav unseen dot → count badge with accessible text (`StudentLayout.tsx:99`); follow-button/CompareTray touch targets ≥40px + confirm on Clear; hover-only related-programs CTA visible on touch (`RelatedSidebar.tsx:119`).

## 5. Testing & verification

Per ship: `tsc -p tsconfig.app.json` 0 · `vite build` 0 · `vitest` green (+ `pytest` for Ship C's migration/schema change). New unit tests: ScrollReset policy (PUSH/POP/tab-param), PageContainer render, usePresence timing, onboarding routing (needs-onboarding → /onboarding → resume), information-architecture redirects untouched. Visual verification via preview on the Discover hub (narrow + xl + font-scale xl) and the wizard. Each ship merges to `main` → auto-deploy → live-bundle grep per standing rule.

## 6. Explicitly out of scope

Institution/admin surfaces (shared primitives benefit them for free); wholesale restyle (Imprint informs motion/onboarding/progress-viz only); DataTable system (Spec 79); axe-CI (Spec 80 tail); container-query plugin; Stage-1 Uni conversation content.

## 7. Follow-ups (noted, not in this round)

- `@tailwindcss/container-queries` for true container-gated rails/grids.
- Replace remaining `animate-pulse` on institution/admin surfaces.
- CLAUDE.md says Profile has 13 tabs; `PROFILE_TABS_SPEC` has 11 — reconcile docs.
- Funnel dashboards once analytics events flow.

## 8. Delivery

Four sequential PRs (A → B → C → D), each verified + deployed before the next starts, per the ship-every-time rule. A and B are pure frontend; C includes one additive migration; D is frontend-only sweeps.
