# 90 · Current MVP vs Spec — Gap Audit

> Inventory of what exists in the current codebase vs. what the Master Paper + Brand Guide call for. Each item carries an action label so a build session can pick up directly.
>
> Status: **draft v1.0** · 2026-05-29 · Source: page-by-page frontend audit (Task #4), service/router inventory, `tailwind.config.js`, `frontend/src/index.css`, `App.tsx`, `App_MVP/CLAUDE.md`.

---

## 1. How to read this audit

For each gap entry:
- **Severity:** `block` (spec not deliverable until fixed) · `major` (spec deliverable degraded) · `minor` (cleanup / polish) · `defer` (Phase E or later).
- **Type:** `remove` (legacy/dead code) · `migrate` (rename/move) · `extend` (add to existing) · `new` (build from scratch) · `wire` (component exists but not connected).
- **Owner:** spec doc that defines the corrected state.
- **Effort:** rough engineering days, single-engineer.

---

## 2. Brand foundation gaps

### G-B1 · Europa font not loaded via Typekit; EB Garamond + Caveat + Kalam still in use
**Severity:** `block` · **Type:** `migrate` · **Owner:** `01-brand-tokens.md` · **Effort:** 0.5 day

`frontend/src/index.css` lines 85, 100, 117, 124, 128 use `EB Garamond`, `Caveat`, `Kalam`. `tailwind.config.js` defines `font-heading: EB Garamond`, `font-hwDisplay: Caveat`, `font-hwNote: Kalam`. The brand guide explicitly says **One Font — Europa**, never a second typeface.

**Corrected font loading:** Europa loads via **Adobe Typekit kit `spe3ioy`** (`@import url('https://use.typekit.net/spe3ioy.css')`, family name lowercase `europa`). NOT self-hosted woff2. The kit ships **300/400/700 only — no Semibold 600** (`--fw-semibold` aliases to 700). See `01-brand-tokens.md` §3.

**Action:**
1. Add the Typekit kit to `frontend/index.html` `<head>` (`<link rel="stylesheet" href="https://use.typekit.net/spe3ioy.css">`). Confirm `app.unipaith.co` + `localhost` are in the kit's domain allowlist and the kit is on the company Adobe account.
2. Update `index.css` to remove the serif heading rule + the `up-hw-*` utility classes; set `h1-h6` to inherit `font-sans` (`'europa', system-ui, …`).
3. Update `tailwind.config.js` `fontFamily` per `01-brand-tokens.md` §8 — `sans/body: ['europa', …]`; remove `heading`, `hwDisplay`, `hwNote`; add the `fontWeight` map (semibold→700).
4. Grep + replace 7 file references to the old fonts.
5. Visual smoke test (Discover, Match, Apply, Profile, Login, Signup, Auth callback). Confirm Europa renders (Network tab shows the Typekit CSS + font files load).

### G-B2 · Brand assets not in `frontend/public/`
**Severity:** `block` · **Type:** `new` · **Owner:** `01-brand-tokens.md` §7 · **Effort:** 0.5 day

`frontend/public/` does not exist. The favicon + wordmark SVGs live only in `/Users/leozhu/Desktop/工作/UniPAith/Brand Materials/`.

**Action:** copy per the asset path table in `01-brand-tokens.md` §7; update `frontend/index.html` favicon links; replace Navbar wordmark img source.

### G-B3 · Proportion rule reconciliation needed
**Severity:** `minor` · **Type:** `migrate` · **Owner:** `01-brand-tokens.md` §2.6 · **Effort:** 0.25 day

PDF says 55·20·15·10; HTML refs say 60·25·10·5. Spec chose 60·25·10·5. Action: confirm with brand owner; document deviation in `01` §10 if reverted.

### G-B4 · Status colors not in current Tailwind config
**Severity:** `major` · **Type:** `extend` · **Owner:** `01-brand-tokens.md` §2.3 · **Effort:** 0.5 day

`tailwind.config.js` has `shadcn destructive` token but no `success` / `warning` / `error` semantic scale (or `success-soft` / dark variants). Some components likely use raw hex (e.g., `text-green-600`) — needs grep + replace.

### G-B5 · Decorative `up-hw-display` / `up-hw-note` utility classes
**Severity:** `minor` · **Type:** `remove` · **Owner:** `01` · **Effort:** 0.25 day

`index.css` lines 124–131. Spec forbids handwriting fonts. Find usages, replace with `font-sans italic` or remove the affordance entirely.

### G-B6 · `tailwind.config.js` `student/school/gold` legacy aliases
**Severity:** `minor` · **Type:** `migrate` · **Owner:** `01` §8 · **Effort:** 1 day

Current config remaps `student-*`, `school-*`, `gold-*`, `cobalt-*` legacy class names to brand values. The aliases worked as a migration shim but the long-term direction is to use semantic tokens (`bg-paper`, `text-ink`, `text-cobalt`). Rename in code over time; leave aliases until grep is clean.

---

## 3. Architecture / IA gaps

### G-A1 · `SchoolDetailPage.tsx` is mis-named — it's the Program Detail Page
**Severity:** `major` · **Type:** `migrate` · **Owner:** `13-detail-pages-program.md` · **Effort:** 0.5 day

`frontend/src/pages/student/SchoolDetailPage.tsx` is routed at both `/s/programs/:programId` and `/s/schools/:programId`. The file should be renamed to `ProgramDetailPage.tsx`. The `/s/schools/:programId` alias should be removed (it routes the same id as a program — confusing for future readers).

### G-A2 · `DiscoverPage.tsx` (886 lines) is legacy dead code
**Severity:** `minor` · **Type:** `remove` · **Owner:** `12-discovery.md` · **Effort:** 0.5 day

Not in `App.tsx` routes. Only re-exported as `DiscoverSearchView` to `explore/SearchView.tsx`, which itself isn't routed. Delete the file; delete `SearchView.tsx`; update any imports.

### G-A3 · `ProgramMatchPage.tsx` (862 lines) is legacy dead code
**Severity:** `minor` · **Type:** `remove` · **Owner:** `11-program-match.md` · **Effort:** 0.5 day

Not in `App.tsx` routes. Replaced by Discover + Explore. Delete.

### G-A4 · Five dead student pages
**Severity:** `minor` · **Type:** `remove` · **Owner:** `04` · **Effort:** 0.5 day

`DashboardPage.tsx` (453), `IntelligenceDashboardPage.tsx` (219), `DecisionComparisonPage.tsx` (552), `ChatPage.tsx` (255), `IntakePage.tsx` (152) — none routed; redirects in `App.tsx` send their old URLs to `/s` or `/s/manage`. Delete.

### G-A5 · Legacy `EssayWorkshopPage.tsx` + `ResumeWorkshopPage.tsx`
**Severity:** `defer` · **Type:** `remove` · **Owner:** `16-workshops.md` · **Effort:** 0.5 day

Per CLAUDE.md "Phase E follow-ups" — kept until `ProfilePage`'s "Essays & Resume" legacy tab is removed. Delete after no remaining `?tab=essays` links.

### G-A6 · `/s/messages/:convId` redirect drops conversation id
**Severity:** `minor` · **Type:** `wire` · **Owner:** `19-inbox.md` · **Effort:** 0.25 day

`App.tsx` line 120: redirects to `/s/manage?tab=messages` without carrying the conversation. Fix: pass through as `&thread=:convId`.

### G-A7 · `components/CommunityTab.tsx`, `CounselorSessionCard.tsx`, `ExploreFeed.tsx`
**Severity:** `minor` · **Type:** `remove` · **Owner:** `04` · **Effort:** 0.25 day

From the pre-Phase-B IA. Verify no consumers, then delete.

---

## 4. Student feature gaps

### G-S1 · Universal Profile — 19 sections vs 13-tab cluster
**Severity:** `major` · **Type:** `extend` · **Owner:** `10-universal-profile.md` · **Effort:** 3 days

Current `ProfilePage.tsx` has 7 tabs (Overview, Identity, Goals, Needs, Strategy, Essays & Resume legacy, Recommenders, Financial). The Overview tab itself spans 18 of 19 spec sections. The spec calls for 13 cluster tabs (per `04-information-architecture.md` §4.6) plus Notifications under Settings. The 19th section (Analytics) is missing.

**Action:**
1. Implement Analytics tab content (profile completeness over time, signal-density-by-category chart, peer-comparison view).
2. Reorganize tabs per `04` §4.6 (collapse Overview's 18-section super-scroll into discrete tabs).
3. Migrate Recommenders + Financial into the Preparation tab.
4. Migrate Essays & Resume legacy out — `16-workshops.md` is the destination.

### G-S2 · Dual-score (fitness + confidence) not surfaced where it matters
**Severity:** `major` · **Type:** `wire` · **Owner:** `11-program-match.md`, `13-detail-pages-program.md`, `15-saved-list.md` · **Effort:** 2 days

`match/DualRing.tsx` exists but `ExplorePage`'s `UniversityCard`/`ProgramCard` still display legacy `match_score`/`match_tier`. `SavedListPage` compare table same. `SchoolDetailPage` reads legacy.

**Action:**
1. Update card components to use `fitness_score` + `confidence_score` from `match_results`.
2. Replace `MatchRing` on detail page with `DualRing`.
3. Compare table: add Confidence column.

### G-S3 · Constraint chips are display-only; not LLM-interpreted + editable
**Severity:** `major` · **Type:** `extend` · **Owner:** `12-discovery.md` · **Effort:** 3 days

ExplorePage NLP search emits ONE summary chip. Spec calls for **each constraint chip individually editable**: click a chip → dropdown for that field → re-runs search.

**Action:**
1. New agent `DiscoveryQueryInterpreter` per `42-ai-agents-claude.md` returns structured constraints, not free-text summary.
2. UI: render each as a separate chip with a clickable editor.
3. Removing a chip updates URL + search.

### G-S4 · ApplicationDetailPage Guardrails tab is cosmetic
**Severity:** `major` · **Type:** `wire` · **Owner:** `17-applications.md` · **Effort:** 2 days

The "Why are you applying?" picker and the rationale capture exist visually but `setGuardrailResult` is voided. Low-fit warning has no scan endpoint.

**Action:**
1. New backend endpoint `POST /me/applications/:id/guardrail-scan` returns `{fit_score_band, recommended_action, blockers}`.
2. Persist student intent + rationale to `applications.intent_picker` + `applications.intent_rationale`.
3. Wire `setGuardrailResult` to the scan response.

### G-S5 · SavedListPage priority state not persisted
**Severity:** `major` · **Type:** `wire` · **Owner:** `15-saved-list.md` · **Effort:** 0.5 day

`considering / planning / applied / dropped` is `useState`-only. Refresh wipes.

**Action:** Add `priority` column to `saved_lists` table; `PATCH /me/saved/:programId` accepts it.

### G-S6 · OnboardingPage is a single-thread stub
**Severity:** `major` · **Type:** `migrate` · **Owner:** `1B-discovery-stage-conversation.md`, `04` · **Effort:** 1 day

Heuristic completion %, no `discovery_sessions` seeding, no track structure. Conflicts with the three-track Discovery model.

**Action:** Either (a) make `/onboarding` a thin shim that creates `discovery_sessions(track='profile', layer='basic')` and redirects to `/s?track=profile`, OR (b) delete `OnboardingPage.tsx` and route signups directly to `/s` with a first-run banner.

### G-S7 · PostsPage Peers tab is "coming soon"
**Severity:** `major` · **Type:** `new` · **Owner:** `04` (Connect surface), pending new spec · **Effort:** 5 days

Spec calls Stage 3a "Connection & Outreach" — Peers is core to it.

**Action:** Define peer model (opt-in profile sharing per program), API, and tab UI in a new spec doc `27-peers-connect.md`. Defer until institution-side relationships are clearer.

### G-S8 · Student SettingsPage missing locale/MFA/password/account-delete
**Severity:** `major` · **Type:** `extend` · **Owner:** `04` §10 · **Effort:** 3 days

Currently notifications + logout only.

**Action:**
1. Locale + timezone selector (server: `student_profiles.locale`, `timezone`).
2. Password change via Cognito API.
3. MFA enroll (TOTP) via Cognito.
4. Account-delete with 30-day grace; soft-delete service.

### G-S9 · Public program/school pages duplicate authenticated components
**Severity:** `minor` · **Type:** `migrate` · **Owner:** `13`, `14` · **Effort:** 1 day

`pages/public/` has its own ProgramDetailPage + InstitutionPage. They should be thin wrappers around the same components with auth-gated CTAs replaced by "Sign in to save".

---

## 5. Institution feature gaps

### G-I1 · ProgramEditorPage uses raw JSON textareas
**Severity:** `major` · **Type:** `extend` · **Owner:** `21-program-detail-page-institution.md` · **Effort:** 4 days

`application_requirements`, `intake_rounds`, `cost_data`, `outcomes_data` are JSON blobs in raw textareas. Admins must hand-author shape. Same in `SettingsPage` for `social_links`, `inquiry_routing`, `support_services`, `policies`, `international_info`, `school_outcomes`.

**Action:** Build guided editors per blob: form-based for known shapes; JSON-with-validation textarea behind an "Advanced" toggle.

### G-I2 · AnalyticsPage charts are hand-rolled CSS bars
**Severity:** `minor` · **Type:** `migrate` · **Owner:** `26-attribution-funnel-analytics.md` · **Effort:** 2 days

No proper chart library used. Workable but underbuilt vs. spec's "executive insights".

**Action:** Adopt `recharts` (already in dependencies if present; otherwise add). Migrate the 4 hand-rolled bars first; keep KPI-card numbers as-is.

### G-I3 · RequirementsChecklistPage drag-reorder not wired
**Severity:** `minor` · **Type:** `wire` · **Owner:** `21` · **Effort:** 0.5 day

`GripVertical` icon present but no DnD. Currently uses sort_order field manually.

**Action:** Add `@dnd-kit` to RequirementsChecklistPage; on reorder, PATCH `/i/programs/:id/checklist/reorder` with new ordering.

### G-I4 · MessagingPage uses polling, not push
**Severity:** `minor` · **Type:** `extend` · **Owner:** (institution messaging — covered in `19`-analog) · **Effort:** 3 days

Auto-refresh every 10s. Spec implies real-time delivery.

**Action:** Add WebSocket or SSE channel for institution messaging; debounce server-side; fall back to polling.

### G-I5 · No fairness/bias dashboard
**Severity:** `block` for `43-data-rights-privacy.md` · **Type:** `new` · **Owner:** `43`, `26` · **Effort:** 5 days

Landing_MVP's `InstitutionFairness.jsx` defines the auto-halt rule: *"if disparate-impact Δ exceeds 0.20 for two consecutive weeks, the model stops scoring new applicants for that cohort."* No dashboard exists to surface this signal to institution staff or to operate the halt.

**Action:**
1. Define metrics: disparate-impact ratio per protected category × cohort × week.
2. Persist signal in `fairness_signals` table.
3. Auto-halt service: when threshold breached for 2 consecutive weeks, set `programs.matching_halted=true`.
4. Dashboard panel: per-cohort 4-week trend + halt status + override workflow (audit-logged).

---

## 6. LLM / AI gaps

### G-AI1 · Existing agents are on OpenAI GPT-4o
**Severity:** `block` for user directive · **Type:** `migrate` · **Owner:** `03-llm-claude-migration.md` · **Effort:** 8 days (full migration), 1 day per agent

10 existing agents — see `03` §4. Plan: add Anthropic provider, then port one agent at a time behind existing flags.

### G-AI2 · AI audit ledger doesn't record provider
**Severity:** `major` · **Type:** `extend` · **Owner:** `03` §8 · **Effort:** 1 day

Current `ai_artifacts` model stores `model_version` but not provider. Per Appendix A spec output (`audit ledger entry bundle (model version + timestamps)`), the spec requires recording provider+model+token counts+consent_mask.

**Action:** Add columns per `03` §8 schema. Existing rows backfill provider=`openai`.

### G-AI3 · Consent mask has no "training" dimension
**Severity:** `major` · **Type:** `extend` · **Owner:** `43-data-rights-privacy.md` · **Effort:** 1 day

Per Master Paper Appendix A output, the 4th dimension is `training`. Current consent UI / schema (per audit) covers email/SMS/marketing-channel toggles only.

**Action:** Add `consent.training` boolean to `student_profiles`; expose in Profile Data Rights tab; enforce in every agent call site per `03` §11.

### G-AI4 · Authenticity risk scoring not implemented
**Severity:** `major` · **Type:** `new` · **Owner:** `35-ai-extensibility.md`, `42-ai-agents-claude.md` · **Effort:** 3 days

Per Master Paper Appendix A: "Authenticity risk flags (generic/over-optimized patterns)" for essays. Aligns with Common App fraud policy.

**Action:** New Haiku agent `AuthenticityRiskScorer` per `42` §17 — scores essays for AI-generated patterns; flag thresholds escalate to integrity signal.

### G-AI5 · DraftSummarizerForReview not implemented
**Severity:** `major` · **Type:** `new` · **Owner:** `31-review-workspace.md`, `42` · **Effort:** 3 days

Per `42` §13 — Opus-tier per-application packet summary for institution reviewers. Currently `StudentDetailPage` has "AI packet summary with regenerate" — confirm it's the same intent and use Opus for the regeneration call.

### G-AI6 · No DiscoveryQueryInterpreter
**Severity:** `major` · **Type:** `new` · **Owner:** `12-discovery.md`, `42` · **Effort:** 2 days

See G-S3. The structured-constraint output is missing.

### G-AI7 · No InboxReplyDrafter
**Severity:** `minor` · **Type:** `new` · **Owner:** `19-inbox.md`, `42` · **Effort:** 2 days

Spec calls for AI-suggested replies in the student inbox (admissions-officer threads). Not implemented.

---

## 7. Data / schema gaps

### G-D1 · Prompt Library schema not fully implemented
**Severity:** `major` · **Type:** `extend` · **Owner:** `40-prompt-library-schema.md` · **Effort:** 10 days

Per Master Paper Appendix A — ~250 input fields + ~150 output fields. Current models cover the core (Profile, Identity, Goals, Needs, Strategy, Match, Applications) but most major-specific fields (CS/Engineering/Business/Health/Arts/Law tracks) are absent.

**Action:**
1. Generate migration adding `student_major_specific_signals` JSONB table per track.
2. Generate migration adding all output-feature inference results to `ai_artifacts` schema with per-field categorization.
3. Wire Adaptive Intake Engine to populate them progressively (per `41`).

### G-D2 · `student_strategies.score_breakdown` and `match_results.match_score` deprecated
**Severity:** `defer` · **Type:** `remove` · **Owner:** `11`, `13` · **Effort:** 1 day

Per CLAUDE.md Phase E follow-up — drop legacy `match_score` and `score_breakdown` once all consumers read `fitness_score` / `confidence_score` directly. Currently `SchoolDetailPage` reads legacy.

### G-D3 · No `peers_connect` data model
**Severity:** `defer` · **Type:** `new` · **Owner:** (future `27`) · **Effort:** 5 days

Connect Peers feature gap (G-S7).

### G-D4 · No `fairness_signals` table
**Severity:** `block` for `43` · **Type:** `new` · **Owner:** `43` · **Effort:** 2 days

For per-cohort disparate-impact tracking + auto-halt (G-I5).

---

## 8. Compliance / privacy gaps

### G-C1 · No formal FERPA + GDPR + CCPA + DPDP compliance review
**Severity:** `block` for institution sales · **Type:** `new` · **Owner:** `43-data-rights-privacy.md` · **Effort:** ongoing

Per Master Paper competitor analysis — every US competitor cites FERPA; EU competitors cite GDPR; India source-market exposure invokes DPDP. **BigFuture's $750K NY AG settlement (2024) is the template UniPaith must avoid.**

**Action:** Engage privacy counsel; complete a SOC 2 Type II readiness assessment in Year 1; publish a Trust page (modeled on Slate, Salesforce Trust Layer).

### G-C2 · No data residency selection per institution
**Severity:** `major` (procurement) · **Type:** `new` · **Owner:** `43` · **Effort:** 30+ days (multi-region infra)

Slate offers US/Canada/EU residency. Salesforce localizes. UniPaith will face the same request from international institutions. Out of MVP scope but tracked for Series A.

### G-C3 · Audit log doesn't cover ALL spec-required event types
**Severity:** `minor` · **Type:** `extend` · **Owner:** `34-audit-log.md` · **Effort:** 1 day

Current covers status_change/decision_release/reviewer_assigned/checklist_change/document_replaced/waiver_override/batch_*. Spec needs to also log: AI-generated artifact accepted/edited/rejected; consent change; data export; account deletion request.

---

## 9. Test gaps

### G-T1 · No integration test for Claude migration
**Severity:** `block` for `03` rollout · **Type:** `new` · **Owner:** `03` · **Effort:** 2 days

CLAUDE.md mandates: "when an LLM agent fails (timeout, parse error, guardrail trip), the service falls back to the rule-based path so the caller never sees a 5xx" — invariant tested by `test_plan2_integration.py`. The migration must preserve this. Add a test that runs each agent through the Claude provider with a mocked failure, asserting rule-based fallback engages.

### G-T2 · No test for `consent.training` enforcement
**Severity:** `major` · **Type:** `new` · **Owner:** `43` · **Effort:** 0.5 day

When `consent.training=false`, no agent should include the student's data in any future training corpus extraction. Add test.

### G-T3 · No test for disparate-impact auto-halt
**Severity:** `major` · **Type:** `new` · **Owner:** `43` · **Effort:** 1 day

Given a synthetic cohort with Δ > 0.20 for 2 consecutive weeks, the matching service must stop scoring new applicants for that cohort. Add test.

---

## 10. Quick reference — top 10 prioritized blockers

| Rank | ID | Title | Severity | Effort |
|---|---|---|---|---|
| 1 | G-B1 | Europa font + remove EB Garamond/Caveat/Kalam | block | 1d |
| 2 | G-B2 | Brand assets into `frontend/public/` | block | 0.5d |
| 3 | G-AI1 | Migrate 10 agents from GPT-4o to Claude | block (user directive) | 8d |
| 4 | G-AI3 | Add `consent.training` dimension | major | 1d |
| 5 | G-AI2 | Audit ledger records provider+model+tokens+consent | major | 1d |
| 6 | G-S3 | Constraint chips (structured + editable) | major | 3d |
| 7 | G-S2 | Wire dual-score across cards + detail + compare | major | 2d |
| 8 | G-I5 | Fairness signal + auto-halt + dashboard | block (43) | 5d |
| 9 | G-S1 | Universal Profile 19-section reorganization | major | 3d |
| 10 | G-S4 | ApplicationDetailPage Guardrails wired | major | 2d |

Top-10 effort total: **~27 engineering-days** for one engineer; ~14 calendar days with two-engineer team and standard rhythms. After top-10 the next 10 items are 30-40 days more.

---

## 11. Items that match the spec well (no action needed)

Per the frontend audit recommendations:
- DiscoverHomePage + sub-folder widgets (TrackSelector, ChatPanel, ArtifactRail, BasicSignalsWidget, IdentitySignalsWidget, GoalStackWidget, NeedsMapWidget) — three-track Phase-B journey faithfully built.
- ExplorePage + ExploreFilters + StrategyView — strategy-first landing with NLP interpretation chip (only the chip-structure gap above).
- ApplicationDetailPage — full status timeline, sidebar checklist, drag-drop S3 documents, AI feedback per essay, readiness modal, offer accept/decline.
- WorkshopsTab + sub-panels — feedback-only contract mechanically and visually honored (matches spec invariant).
- PipelinePage — DnD kanban + bulk actions + 5 views match the admissions-OS spec exactly.
- StudentDetailPage (institution) — full review packet with AI assistant, AI prefill, AI summary, AI draft, integrity scan, scoring rubric, decision + offer.
- SegmentsPage + CampaignsPage + TemplatesPage + PostsPage — marketing/CRM stack unusually complete for an MVP.
- AuditLogPage — covers correct event types (extension G-C3 above).

---

## 12. Items the spec extends BEYOND the current MVP (new scope)

These are features in the Master Paper / Business Methodology / Landing_MVP that don't have any current implementation. They are NOT regressions; they are new build work.

- Peers (Connect Stage 3a) — currently "coming soon" placeholder.
- Authenticity Risk Scorer (essay anti-AI-pattern flagging).
- Inbox AI reply drafter (student side).
- Per-cohort fairness signal + auto-halt.
- Major-specific Prompt Library expansion (CS, Engineering, Business, Health, Arts, Law track-specific signals).
- Data residency election per institution.
- Multi-institution staff users (switch-tenant UI).
- Bedrock as a third LLM provider.
- Streaming for DiscoveryOrchestrator.
- Multi-channel notifications (SMS, push, in-app for students).

---

## 13. Cleanup punch list (in priority order)

For a "clean up the codebase" session (no new feature work):

1. G-A1 — rename `SchoolDetailPage.tsx` → `ProgramDetailPage.tsx`; remove `/s/schools/:programId` alias.
2. G-A2, G-A3, G-A4 — delete 5 dead student pages + 2 legacy pages.
3. G-A7 — delete 3 dead component files.
4. G-A6 — fix `/s/messages/:convId` redirect to carry the id.
5. G-B5 — delete handwriting utility classes.
6. G-B6 — replace `student-*`/`school-*` Tailwind aliases with semantic tokens grep-and-replace.
7. Run linter; fix.

Estimate: 2 engineering days.
