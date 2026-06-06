# Student-Side Comprehensive QA — Design

> Goal: bring the entire UniPaith **student** app (`app.unipaith.co/s…`) up to standard — free of bugs, visually and functionally clean, fully on-brand (Spec/01 tokens + emotional-design system), and achieving the goals in the spec set. Audited via 9 parallel surface agents against the governing specs + brand. Scope approved by user: **A–J (everything, including the 4 stretch features)**, full-stack, ship-to-prod.

- **Date:** 2026-06-06 · **Owner:** QA session (junczhu-ui) · **Branch:** `claude/bold-bouman-a040c3`
- **Source of truth:** `Spec/01-brand-tokens.md` (brand), `Instructions/student_emotional_design_system.md` (tone/urgency), per-surface specs (`08`–`21`, `42`–`44`, `53`, `56`, `76`–`81`), `CLAUDE.md` (IA + detail-page rules).
- **Baseline health:** `tsc -b` exit 0; 0 forbidden fonts; 1 stray `bg-white`; Europa-only holds. Codebase is well-built — this is a polish/correctness/consistency sweep, not a rebuild.

## Brand & emotional-design principles (applied on every edit)

1. **Gold is punctuation, not fill (~5%).** Reserve `--primary` for the DualRing fitness arc, the single earned beat (enrollment confirm), and one primary CTA per region. Cobalt (`--secondary`) is the workhorse accent for icons, links, interactive states, AI attribution.
2. **Hierarchy from the type system.** Eyebrows use the `text-eyebrow` token + `text-muted-foreground`; meta/secondary text uses `text-muted-foreground`; **never italic for UI**.
3. **Tokens only.** No raw hex / `bg-white` / `text-black` in student code; dark-mode parity via semantic tokens.
4. **Calm confidence, not panic.** Red only for true blockers; grade deadline urgency gentle (30+d) → amber (8–30d) → red (≤7d/overdue). Every AI inference editable + "why this appears". Empty states always carry a concrete next action. Reassurance micro-copy ("Saved", "on track"). No shame framing ("incomplete", "Just starting"); no internal jargon ("SMART", "Maslow-keyed", "extract").
5. **Every surface renders loading / empty / error / edge** (Spec 78). Error ≠ empty. Shared `QueryError` + `ConfirmDialog`.
6. **Detail pages**: `max-w-5xl mx-auto` everywhere (verified consistent); campus-photo hero → cream, no logo/geo; Niche-modeled real-data content + sourced citation.

## Workstreams

Each workstream is a coherent batch: edit → `tsc`/`vitest` green → preview screenshot-verify → commit. The full per-file/`:line` finding list lives in the implementation plan.

- **A — Functional bugs + destructive-action guards.** `text-on-primary`→`text-primary-foreground` (TrialBanner, PublicLayout); de-dupe `generateStrategy` double-POST; Interviews query-key `appId`; ChatPanel counselor-avatar inversion; MFA recovery-codes-before-verify; `isError` discarding stale data (SavedListPage); dead identical ternary; ESC/focus-trap on EventDetailModal + ManageFollowingPanel (→ `Sheet`); curly-apostrophe cleanup; `ConfirmDialog` on remove-saved / unfollow / delete-search / cancel-plan / unfollow-institution. *(Verified: `decision==='admitted'` is NOT a bug — backend allows both; leave intact.)*
- **B — Error + loading states (Spec 78).** Add `isError`→`QueryError` (Connect Updates/Events/Peers/PostsPage, SettingsPage, Profile Goals/Needs/Identity, MatchesSection error≠sparse). Add skeletons (Discover rail widgets, StrategyView null→skeleton, Profile Goals/Needs/Identity, App-detail essays/recommenders/interviews, CompletionRing). `lib/copy.ts` for shared error strings.
- **C — Earned-gold discipline (Spec 01/76).** Sweep gold misuse → cobalt/neutral across Discover widgets, ExploreFilters, StrategyView, RationalePopover, PromoCard (`border-l-student`→cobalt), program-detail (AboutCard/NextStepsCard/RelatedSidebar/KeyMetrics amber), Apply (SuggestedReplyCard/ApplyReadyChecklist/ApplicationsPage star/ThreadView Sparkles), Workshops (tab/bars/Final/Sparkles), Profile (TimelineTab dots/StrategyTab stub), TrialBanner, OnboardingPage (one gold CTA).
- **D — Text hierarchy & eyebrows.** `text-eyebrow`+`text-muted-foreground` for eyebrows; meta/subtitle→muted; remove 23 italic UI strings; density `PageHeader` on PostsPage/SettingsPage/RecommendationsPage.
- **E — DualRing / dual-score (Spec 09/76).** ProgramCard `MatchDot`→`DualRing` (fitness+confidence); canonical reach/target/safer via `BandBadge`; SavedListPage sort label fitness; StrategyView freshness; RationalePopover title "Why this match".
- **F — Calm urgency & tone/copy.** Graded urgency colors (Calendar dynamic-by-days, Connect 7-day red, must-have needs amber, missing-item circles muted); de-jargon + warm empty-states + reassurance; Workshop voice "I"→"we" (feedback-only invariant already holds — preserve).
- **G — AI attribution consistency (Spec 37/45).** Shared `<AIBadge>` everywhere (StrategyTab, IdentityTab inline badges); cobalt not gold Sparkles (Workshops, ThreadView, ReadinessHeader); stub badge loses misleading Sparkles; backend `WorkshopFeedbackResponse.model_used` + frontend wire → AIBadge on real AI path.
- **H — Accessibility (Spec 80).** Profile tabs `aria-controls`/`role=tabpanel`/arrow-keys; score-ring `aria-label` (ReadinessHeader/TrackReadinessHeader); ArtifactRail `aria-label`; `useAnnounce()` + `aria-live` region in StudentLayout wired to key optimistic actions; offline banner (`useOnlineStatus`).
- **I — Spec-gaps / content depth.** SchoolSubunitPage Niche content (scoped stats/outcomes/quick-facts) + citation; Profile completion "what this unlocks" framing; FinancialTab AidLikelihoodCard; CompareTray best-value highlight; `start_term` chip editor; dead-code cleanup (MatchRing/MatchSummary/InfoPillRow/ProgramHeader geo).
- **J — Stretch (large, full-stack).**
  - **J1 Discover SSE token-streaming** (Spec 77 §6): backend SSE endpoint streaming orchestrator tokens; frontend `EventSource`/stream consumer in ChatPanel; cobalt streaming caret; live artifact-rail update on `extracted_signals`; typing indicator only pre-first-token; reduced-motion + fallback to current request/response path.
  - **J2 Connect feed infinite-scroll + "new posts" pill** (Spec 56 §4): cursor pagination (`{items,next_cursor}`) + `useInfiniteQuery` + scroll sentinel; seen-state → "↑ N new" pill.
  - **J3 Compare side-by-side sheet** (Spec 10 §8): `CompareSheet` (5 dimension rows: structure/location/cost/access/outcomes) opened from CompareTray + `?compare=open`.
  - **J4 First-run coachmarks** (Spec 81 §3.3): one-time tooltips for DualRing, rationale popover, compare tray, keyed off `ui-store`.

## Risk & sequencing

Order: **A → B → (C, D in tandem) → E → F → G → H → I → J**. Bugs/states first (stabilize), then brand sweeps (broad but low-risk), then dual-score/UX, then a11y/spec-gaps, then the J features last (highest risk, each its own commit + preview verification). Cross-cutting sweeps (C/D/G) done as careful per-file passes — not parallel file-mutation — to avoid conflicts. Backend touches (J1 SSE, J2 cursor/seen-state, G `model_used`, I AidLikelihood endpoint if absent) gated behind feature flags / fallbacks so the deterministic path stays default and no 5xx ever reaches the student.

## Definition of done

- `tsc -b` 0, `vitest` green, `eslint` clean; backend `pytest` green for any backend touch.
- Every changed student surface preview-verified (light + dark) with a screenshot.
- Brand checklist (Spec 01 §9) passes per changed surface; gold proportion respected.
- Committed in logical batches → merged to `main` → deployed → **verified live** on `app.unipaith.co` (and `api.unipaith.co` for backend). Working tree clean, `main` at new commit.
