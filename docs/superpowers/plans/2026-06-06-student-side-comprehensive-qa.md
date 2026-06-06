# Student-Side Comprehensive QA — Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax. Execute workstream-by-workstream; each ends with `tsc`/`vitest`/preview verify + commit. Cross-cutting sweeps (C/D/G) are careful per-file passes, NOT parallel file-mutation.

**Goal:** Bring the UniPaith student app to standard — bug-free, on-brand, accessible, spec-complete (A–J, full-stack), shipped live.

**Architecture:** React 19 + TS + Vite + Tailwind (semantic tokens) + Zustand + TanStack Query frontend; FastAPI backend for the few full-stack touches (J1 SSE, J2 cursor/seen, G model_used). Verify per surface in preview (light+dark), commit in batches, merge→deploy→verify live.

**Tech Stack:** frontend/ (vitest, eslint, tsc -b); unipaith-backend/ (pytest, AI_MOCK_MODE). Run from worktree; node_modules symlinked from main.

---

## Verification protocol (every workstream)
- [ ] `cd frontend && npx tsc -b` → exit 0
- [ ] `cd frontend && npx vitest run` → green
- [ ] `cd frontend && npx eslint src/` → clean (warnings ok)
- [ ] preview: reload, snapshot/screenshot changed surface light + dark
- [ ] commit with conventional message; push when workstream batch is verified

---

## Task A — Functional bugs + destructive-action guards

**Files:** TrialBanner.tsx, PublicLayout.tsx, DiscoverHomePage.tsx, discover/ReadinessRail.tsx, discover/ChatPanel.tsx, discover/NeedsMapWidget.tsx, ApplicationDetailPage.tsx, settings/SecurityCard.tsx, SavedListPage.tsx, connect/EventsTab.tsx, connect/ManageFollowingPanel.tsx, saved/SavedProgramRow.tsx, saved/SavedSchoolCard.tsx, saved/SavedSearchesPanel.tsx, settings/BillingCard.tsx + curly-apostrophe files.

- [ ] `TrialBanner.tsx:55` + `PublicLayout.tsx:35`: `text-on-primary` → `text-primary-foreground` (broken non-token class).
- [ ] Discover double-POST: remove the `generateStrategy` mutation from `ReadinessRail.tsx:252-261`; lift to a single `onGenerateStrategy` prop passed from `DiscoverHomePage` (which already owns `StrategyHandoffCTA` at :107-116). Render only one CTA path.
- [ ] `ApplicationDetailPage.tsx:710`: Interviews query key `['interviews']` → `['interviews', appId]`; keep client filter.
- [ ] `ChatPanel.tsx` EmptyState (~:196): replace student `<Avatar>` on the counselor opener with the counselor `Sparkles`-in-`bg-muted` circle (match MessageBubble ~:64).
- [ ] `NeedsMapWidget.tsx:109`: remove dead identical ternary `isFilled ? 'text-foreground' : 'text-foreground'` → `'text-xs font-medium text-foreground'`.
- [ ] `SecurityCard.tsx:441-453`: move recovery-codes block to render only after `confirmMut.onSuccess` (post-TOTP-verify), not from the enroll response.
- [ ] `SavedListPage.tsx:255`: change `if (isError)` → `if (isError && programs.length === 0)` so stale data + inline banner (:343) shows.
- [ ] Convert `EventsTab.tsx` EventDetailModal (~:284) and `ManageFollowingPanel.tsx` (~:28) to the shared `Sheet` (ESC + focus-trap + `role=dialog`). Fix `text-foreground hover:text-foreground` close buttons → `text-muted-foreground hover:text-foreground`.
- [ ] Curly→straight apostrophes in code string literals: `ChatPanel.tsx` ALWAYS_REPLIES, `BillingCard.tsx:37` toast, and the other flagged files (CalendarPage, MessagesPage, OnboardingPage, SavedSearchesPanel, ApplyReadyChecklist, EnrollmentPanel, ChipControls, SaveSearchButton) — only where the `’` is in a JS string used in logic/keys; leave display copy that intentionally uses typographic quotes.
- [ ] ConfirmDialog guards (use existing `confirmDialog()` helper): `SavedProgramRow.tsx:232` remove; `SavedSchoolCard.tsx:35` unfollow; `SavedSearchesPanel.tsx:114` delete; `BillingCard.tsx:146` cancel-plan; `ManageFollowingPanel` unfollow.
- [ ] Verify protocol + commit: `fix(student): correctness bugs + destructive-action confirmations`

## Task B — Error + loading states (Spec 78)

**Files:** connect/UpdatesTab.tsx, EventsTab.tsx, PeersTab.tsx, PostsPage.tsx, SettingsPage.tsx, profile/GoalsTab.tsx, NeedsTab.tsx, IdentityTab.tsx, match/MatchesSection.tsx, match/StrategyView.tsx, discover widgets, ApplicationDetailPage.tsx, ProfilePage.tsx, lib/copy.ts (new).

- [ ] Create `frontend/src/lib/copy.ts` exporting shared error strings (`ERR_LOAD`, `ERR_RETRY`, `OFFLINE`, etc.).
- [ ] Add `isError` → `<QueryError onRetry={refetch} />` to: UpdatesTab, EventsTab, PeersTab, PostsPage follow-count, SettingsPage:20, GoalsTab, NeedsTab, IdentityTab.
- [ ] `MatchesSection.tsx`: add `isError && !matches.length` branch = "Couldn't reach the matching service" + Retry, distinct from the sparse-profile empty state.
- [ ] `StrategyView.tsx:90`: `return null` during load → skeleton card.
- [ ] Skeletons: Discover rail widgets (`GoalStackWidget`/`NeedsMapWidget`/`IdentitySignalsWidget`/`BasicSignalsWidget`/`PersonalitySignalsWidget` "Loading…" → `<Skeleton>`); Profile Goals/Needs/Identity bare-text loading → `SkeletonCard`; `ApplicationDetailPage` essays/recommenders/interviews tabs destructure `isLoading` → skeleton; `ProfilePage.tsx:74` CompletionRing skeleton during load.
- [ ] Verify + commit: `fix(student): error + loading states on all query surfaces`

## Task C — Earned-gold discipline (Spec 01/76)

Sweep gold misuse → cobalt (`secondary`) / neutral. Keep gold only on DualRing fitness arc, enrollment beat, one primary CTA/region. Per-file:
- [ ] discover: `GoalStackWidget` (icons/links/dots), `NeedsMapWidget`, `IdentitySignalsWidget` (chips `bg-primary/10`→`bg-secondary/10`; Manage links), `PersonalitySignalsWidget` ConfidenceDots `bg-primary`→`bg-secondary`.
- [ ] `explore/shared/ExploreFilters.tsx` (358/385/390/421/433/438): interactive gold → secondary; `bg-white/20` (:363) → `bg-background/20`.
- [ ] `match/StrategyView.tsx` (109/112/135/138/179): empty-state tints + Target icon → secondary/muted.
- [ ] `match/RationalePopover.tsx:108`: citation chips `border-primary bg-primary/10` → secondary.
- [ ] `explore/cards/PromoCard.tsx:15`: `border-l-student` (undefined) → `border-l-secondary`.
- [ ] program detail: `AboutCard.tsx` (79/100/104/106), `NextStepsCard.tsx:107`, `RelatedSidebar.tsx` (50/55/93/101/123) gold→secondary; `KeyMetrics.tsx` amber tone `bg-warning` → neutral `bg-muted`/foreground.
- [ ] apply: `SuggestedReplyCard.tsx:40` `border-accent/40`→`border-border`; `ApplyReadyChecklist.tsx` (45/50/61) accent→success/secondary; `ApplicationsPage.tsx:316` star `text-primary`→`text-secondary`; `ThreadView.tsx` (186/285) Sparkles `text-accent`→`text-muted-foreground`.
- [ ] workshops: `WorkshopsTab.tsx:83` active tab gold→secondary; `TrackReadinessHeader.tsx:92` bars gold→secondary scale; `ResponseEditor.tsx:189` "Final" gold→secondary; `ReadinessHeader.tsx:115`+`TrackReadinessHeader.tsx:140` Sparkles gold→secondary (or AIBadge in G).
- [ ] profile: `TimelineTab.tsx:86` dots gold→secondary (gold only for decision events); `StrategyTab.tsx` stub badge Sparkles removed (G).
- [ ] `TrialBanner.tsx:55` upgrade button gold→`variant=secondary`; `OnboardingPage.tsx`: keep ONE gold CTA (step-2 "Start exploring"), step-0 "Get started" → secondary.
- [ ] Verify + commit: `style(student): enforce earned-gold proportion (gold→cobalt sweep)`

## Task D — Text hierarchy & eyebrows

- [ ] Replace hand-rolled eyebrows `text-[10px] uppercase tracking-wide text-foreground` → `text-eyebrow uppercase text-muted-foreground` (discover widgets, workshops panels, StrategyView, ProbabilityBands, match labels).
- [ ] Meta/subtitle/secondary `text-foreground` → `text-muted-foreground` across flagged lines (connect cards, workshops result panels, ApplicationDetailPage helper text, PostsPage subtitle, ApplicationsPage helper, DualRing micro-labels).
- [ ] Remove `italic` from the 23 UI strings (discover widget empties, InterviewPracticePanel `q.why`, IdentityTab empties, etc.) → normal weight muted.
- [ ] Density `PageHeader`/`SectionHeader` on PostsPage, SettingsPage, RecommendationsPage.
- [ ] Verify + commit: `style(student): text hierarchy, eyebrow tokens, kill italic UI`

## Task E — DualRing / dual-score (Spec 09/76)

- [ ] `explore/cards/ProgramCard.tsx`: replace `MatchDot` (single gold arc) with `DualRing` (fitness+confidence); remove `MatchDot` fn.
- [ ] ProgramCard fit badge: use `band_label` (reach/target/safer) via `BandBadge`, not legacy `match_tier` ad-hoc labels.
- [ ] `SavedListPage.tsx:57,369`: sort key/label prefer `fitness_score` ("Fitness score").
- [ ] `match/StrategyView.tsx`: add `relativeTime(strategy.generated_at)` to collapsed header.
- [ ] `match/RationalePopover.tsx:78`: title "Why this score?" → "Why this match".
- [ ] Verify + commit: `fix(student): DualRing + canonical bands on Match cards`

## Task F — Calm urgency & tone/copy

- [ ] Graded urgency colors: `CalendarPage.tsx` TYPE_META deadlines — derive dot color by `daysUntil` (>30 warning, ≤7/overdue error, else neutral); `connect/ConnectCards.tsx` DeadlineCard 14-day red → 7-day; `profile/NeedsTab.tsx` must_have `danger`→`warning`/info; `NeedsMapWidget.tsx:117` must-have red→foreground; `ApplicationDetailPage.tsx:887` missing-item circles red→muted.
- [ ] De-jargon: GoalsTab "SMART goals"→"Your goals" (SMART in subtitle); NeedsTab "Maslow-keyed" subtitle→plain; IdentitySignalsWidget "extract"→warmer; `ReadinessHeader.tsx:16` "Just starting"→"Getting started".
- [ ] Warm empty-states w/ CTA: IdentityTab empties → `<EmptyState>` + action; OverviewTab empty next-actions → link to Apply/Connect.
- [ ] Workshop voice: WorkshopsTab.tsx:53 "I…" → "We…"; preserve feedback-only invariant (no generation UI).
- [ ] Verify + commit: `fix(student): calm-urgency colors + de-jargon + warm empty states`

## Task G — AI attribution consistency (Spec 37/45)

- [ ] Replace inline custom AI badges with shared `<AIBadge>`: `StrategyTab.tsx:131`, `IdentityTab.tsx:451`.
- [ ] Cobalt not gold Sparkles for AI: Workshops `ReadinessHeader`/`TrackReadinessHeader`, `ThreadView`, others — or swap to `<AIBadge>`.
- [ ] `StrategyTab.tsx:138-141` stub badge: remove misleading `<Sparkles>`.
- [ ] Backend: add `model_used: str | None` to `unipaith-backend/src/unipaith/schemas/workshop_feedback.py` WorkshopFeedbackResponse; populate in workshop_feedback_service; mirror in `frontend/src/types/index.ts` WorkshopFeedbackRun; render `<AIBadge fallback={run.is_stub} />` in the rubric-scores header. pytest the schema.
- [ ] Verify (tsc+vitest+pytest) + commit: `feat(student): consistent AIBadge attribution + workshop model_used`

## Task H — Accessibility (Spec 80)

- [ ] `ProfilePage.tsx:85-103`: tab buttons get `id`, `aria-controls`, `aria-selected`; panel wrapped `role=tabpanel aria-labelledby`; add Left/Right/Home/End arrow-key handler on the tablist.
- [ ] Score rings: add `role="img" aria-label="{score} out of 100 — {band}"` to SVG in `ReadinessHeader` + `TrackReadinessHeader`.
- [ ] `discover/ArtifactRail.tsx:31`: `<aside aria-label="Discovery signals">`.
- [ ] Create `frontend/src/hooks/useAnnounce.ts` + a single `<div aria-live="polite" className="sr-only">` mounted in `StudentLayout`; wire to key optimistic actions (save-to-list, RSVP, stage move).
- [ ] Create `frontend/src/hooks/useOnlineStatus.ts`; render an offline banner above TrialBanner in `StudentLayout` when `!navigator.onLine`.
- [ ] Verify + commit: `feat(a11y): tab semantics, ring labels, live-region announcer, offline banner`

## Task I — Spec-gaps / content depth

- [ ] `SchoolSubunitPage.tsx`: add Niche-modeled content — pull parent-institution outcomes/ranking scoped to the school (or school-level aggregates: acceptance band, program count, degree types, median tuition) + a sources citation footer matching ProgramDetailPage pattern. Replace placeholder "A full profile…is on the way" copy with neutral empty state.
- [ ] Profile completion "unlocks": add `hint` to `CATEGORY_META` in `profile/shared.tsx`; surface one-line `text-xs text-muted-foreground` under each cluster's dots in `OverviewTab`.
- [ ] `profile/FinancialTab.tsx`: add `AidLikelihoodCard` reading `aid_scholarship_likelihood_band`; if no backend endpoint exists, add a read-only one (deterministic) behind existing financial service.
- [ ] `CompareTray.tsx`: best-value highlight (`text-secondary font-semibold`) on top fitness/confidence column per row (`compareDimensions.ts`).
- [ ] `explore/discovery/ChipControls.tsx`: add `start_term` editor branch (season select + year).
- [ ] Dead-code cleanup: delete `program/MatchRing.tsx`, `program/MatchSummary.tsx`, `program/InfoPillRow.tsx` (unused, wrong-shape) and remove geo line from `program/ProgramHeader.tsx:250-255` (or delete if unused) — confirm no imports first.
- [ ] Verify + commit: `feat(student): SchoolSubunit content, completion unlocks, aid likelihood, compare highlight`

## Task J1 — Discover SSE token-streaming (Spec 77 §6)

**Files:** backend api/discovery route, frontend discover/ChatPanel.tsx, api/discovery.ts.
- [ ] Backend: add an SSE streaming variant of `POST /me/discovery/sessions/{id}/messages` (e.g. `?stream=1` or `/messages/stream`) that yields orchestrator tokens then a final `extracted_signals` event; keep the existing non-stream endpoint as fallback. Guard behind existing `ai_discovery_v2_enabled`; deterministic path returns the full message as one chunk.
- [ ] Frontend: in `ChatPanel`, consume the stream via `fetch`+`ReadableStream` (EventSource can't POST); render incremental assistant text with a cobalt streaming caret; show typing indicator only until first token; on the final signals event invalidate the artifact-rail queries. Fall back to the current `useMutation` path on stream error or when `prefers-reduced-motion` (render full response).
- [ ] Verify (tsc+vitest+pytest) + preview (watch tokens stream) + commit: `feat(discover): SSE token-streaming with deterministic fallback`

## Task J2 — Connect infinite-scroll + new-posts pill (Spec 56 §4)

**Files:** backend connect_service/api, frontend api/connect.ts, connect/UpdatesTab.tsx.
- [ ] Backend: return `{items, next_cursor}` from the connect feed (cursor = created_at+id); accept `cursor` param. Add a lightweight seen-state (last-seen cursor per user) or compute "new since" client-side from a stored timestamp.
- [ ] Frontend: `useInfiniteQuery` with cursor + IntersectionObserver scroll sentinel; "↑ N new posts" pill when newer items exist since last view; tapping scrolls-to-top + refetches.
- [ ] Verify + preview + commit: `feat(connect): cursor pagination, infinite scroll, new-posts pill`

## Task J3 — Compare side-by-side sheet (Spec 10 §8)

**Files:** new components/student/CompareSheet.tsx, CompareTray.tsx, ExplorePage.tsx.
- [ ] Build `CompareSheet` (Sheet/modal) with 5 dimension rows (structure, location, cost, access, outcomes) reusing `compareDimensions.ts`; best-value highlight per row.
- [ ] Open from CompareTray "Open compare" CTA and from `?compare=open` (parse in ExplorePage).
- [ ] Verify + preview + commit: `feat(explore): side-by-side compare sheet`

## Task J4 — First-run coachmarks (Spec 81 §3.3)

**Files:** new components/ui/Coachmark.tsx (or Tooltip), ui-store, DualRing/RationalePopover/CompareTray call sites.
- [ ] Add one-time coachmark flags to `ui-store`; build a small `Coachmark` (popover tooltip, dismiss-once).
- [ ] Attach to DualRing (first match card), rationale popover trigger, compare tray — show once, persist dismissal.
- [ ] Verify + preview + commit: `feat(student): first-run coachmarks for signature components`

---

## Ship (after all tasks verified)
- [ ] Full `tsc -b` + `vitest` + `eslint` + backend `pytest` green.
- [ ] Merge branch → `main`; confirm deploy (frontend S3+CloudFront invalidation; backend ECS).
- [ ] Verify live: `app.unipaith.co/s` loads, changed surfaces correct light+dark; `api.unipaith.co` healthy; `/goal` hub unbroken.
- [ ] Working tree clean; `main` at new commit.

## Self-review notes
- Spec coverage: A–J map 1:1 to the design doc workstreams; every audit finding has a task line.
- The `decision==='admitted'` finding is intentionally excluded (verified non-bug).
- Backend touches (J1, J2, G) all keep a deterministic fallback so no 5xx reaches the student.
