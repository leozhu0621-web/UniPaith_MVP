# 48 · Build Sequencing — Phased Roadmap from Current MVP → Master Paper Spec

> The order in which to build, with dependencies and parallelization opportunities called out. Each phase = one Claude Code session (or one engineer-sprint), scoped to ~5–10 engineering days.
>
> Status: **draft v1.0** · 2026-05-29 · Depends on `47-current-vs-spec-gap-audit.md` for gap detail.

---

## 1. Phase-0 — environment health (every session begins here)

Per `App_MVP/CLAUDE.md` Pre-Work Checklist. Before any feature work in a fresh session:

```bash
# 1. DB up
make dev-db                   # Postgres via Docker
# 2. Backend up
make dev-backend              # migrations + uvicorn :8000
# 3. Frontend up
make dev-frontend             # vite :5173
# 4. Tests green
make test-backend             # 177+ tests
make test-frontend            # vitest
# 5. Lint clean
make lint
```

If anything fails, fix the environment before starting feature work. **Do not skip.**

---

## 2. Phase ordering — the critical path

```
Phase 1 — Brand foundation       (visual ground truth)
   ↓
Phase 2 — Claude LLM migration   (provider abstraction; per-agent port)
   ↓
Phase 3 — Cleanup punch list     (dead code; rename; redirect fixes)
   ↓
Phase 4 — Data spine             (Prompt Library schema + migrations)
   ↓
Phase 5 — Discovery completeness (constraint chips; query interpreter; 3-track flow polish)
   ↓
Phase 6 — Universal Profile expansion (19 sections + tab reorganization)
   ↓
Phase 7 — Match dual-score wiring (DualRing on cards + detail + compare)
   ↓
Phase 8 — Applications & Workshops polish (Guardrails wired; checklist gate; resume/essay deletion)
   ↓
Phase 9 — Saved list persistence
   ↓
Phase 10 — Institution Editors guided forms (replace raw JSON textareas)
   ↓
Phase 11 — Fairness signal + auto-halt
   ↓
Phase 12 — Authenticity risk + AI assistive layer expansion
   ↓
Phase 13 — Peers / Connect Stage 3a (NEW)
   ↓
Phase 14 — Data residency, multi-tenant, Bedrock (deferred)
```

Some phases can run in parallel — see §3.

---

## 3. Parallelizable workstreams

These can be picked up by separate sessions without conflict:

| Workstream A (Frontend) | Workstream B (Backend) | Workstream C (Data) |
|---|---|---|
| Phase 1 — Brand | Phase 2 — Claude | Phase 4 — Prompt Library migrations |
| Phase 5 — Discovery chips | Phase 11 — Fairness signal | Phase 9 — Saved priority persistence |
| Phase 7 — DualRing wiring | Phase 12 — AI assistive layer | |
| Phase 10 — Guided editors | | |

Constraint: Phase 2 and Phase 4 should both complete before Phase 8 (Applications uses both Claude agents and Prompt Library fields).

---

## 4. Phase 1 — Brand foundation

**Goal:** every screen renders in the Europa-only, Sunlit-Gold + Cobalt-on-Paper system. Brand assets live in `frontend/public/`.

**Specs:** `01-brand-tokens.md`, `02-design-system.md`.
**Gap items:** G-B1, G-B2, G-B3, G-B4, G-B5, G-B6.
**Effort:** 3–4 days.

**Steps:**
1. Copy brand assets from `Brand Materials/` to `frontend/public/`.
2. Acquire Europa fonts; place `.woff2` files in `frontend/public/fonts/`.
3. Rewrite `tailwind.config.js` per `01` §8.
4. Rewrite `frontend/src/index.css` to remove EB Garamond, Caveat, Kalam; update body/heading rules to use Europa stack.
5. Update `frontend/index.html` favicon links.
6. Update Navbar wordmark img src.
7. Grep and replace 7 files referencing handwriting/serif fonts.
8. Visual smoke test: Login, Signup, Auth Callback, Discover, Match, Apply, Connect, Profile, Saved, Settings, Institution Dashboard, Pipeline, Programs.
9. Dark mode spot-check on 3 representative screens.

**Done when:** no reference to `EB Garamond`, `Caveat`, `Kalam` in `frontend/src`; favicon shows the UP monogram in browser tab; all 11+ screens look as the brand guide intends.

---

## 5. Phase 2 — Claude LLM migration

**Goal:** every LLM call site routes through the Claude provider; OpenAI remains as a parallel fallback; rule-based fallback preserved.

**Specs:** `04-llm-claude-migration.md`, `45-ai-agents-claude.md`.
**Gap items:** G-AI1, G-AI2.
**Effort:** 8 days.

**Steps:**
1. Add `anthropic` Python SDK to `unipaith-backend/pyproject.toml`.
2. Build `services/ai/providers/{base.py, anthropic.py, openai.py, registry.py}` per `04` §5.
3. Add env vars; AWS Secret for `ANTHROPIC_API_KEY`; `ecs.tf` update.
4. Extend `ai_artifacts` model to add `provider`, `model_id`, token-counts, `cache_*_tokens`, `consent_mask` columns; Alembic migration.
5. Per-agent port order: Extractor → Validator → Identity → MatchRationale → Workshops trio → Strategy → Orchestrator → Judge.
   - Each agent: write Claude prompts with system+persona cache breakpoints; wire structured output validation; write integration test for rule-based fallback; flag flip behind `AI_PROVIDER_DEFAULT`.
6. Add `/health/ai` probe.
7. Soak each agent in dev → staging → prod-canary one at a time.

**Done when:** all 10 existing agents on Claude in dev; ledger writes provider+model; fallback tests green.

---

## 6. Phase 3 — Cleanup punch list

**Goal:** remove ~3,000 lines of dead code; fix mis-naming; fix one redirect.

**Specs:** `47` §13.
**Gap items:** G-A1, G-A2, G-A3, G-A4, G-A6, G-A7, G-B5, G-B6.
**Effort:** 2 days.

**Steps:**
1. Rename `SchoolDetailPage.tsx` → `ProgramDetailPage.tsx`; remove `/s/schools/:programId` alias.
2. Delete: `DiscoverPage.tsx`, `ProgramMatchPage.tsx`, `DashboardPage.tsx`, `IntelligenceDashboardPage.tsx`, `DecisionComparisonPage.tsx`, `ChatPage.tsx`, `IntakePage.tsx`, `SearchView.tsx`, `SavedView.tsx`, `CommunityTab.tsx`, `CounselorSessionCard.tsx`, `ExploreFeed.tsx`.
3. Fix `/s/messages/:convId` redirect to carry the id.
4. Delete `up-hw-display` / `up-hw-note` utility classes.
5. Grep + replace `student-*`, `school-*`, `gold-*` Tailwind aliases with semantic tokens. Remove aliases from `tailwind.config.js`.
6. Run linter; fix.
7. Smoke test.

**Done when:** route map matches `05-information-architecture.md` exactly; codebase has ~3,000 fewer lines; lint clean.

---

## 7. Phase 4 — Data spine (Prompt Library)

**Goal:** all input categories from `42-prompt-library-schema.md` have models, migrations, and CRUD endpoints. Major-specific tracks are JSONB-stored. Output schema columns on `ai_artifacts`.

**Specs:** `42-prompt-library-schema.md`, `44-adaptive-intake-engine.md`.
**Gap items:** G-D1, G-AI3.
**Effort:** 8–10 days.

**Steps:**
1. Per `42` §8, add the NEW tables and extend the existing ones.
2. Alembic migrations.
3. Add `consent.training` to the `student_consent` table.
4. Add `student_major_specific_signals` JSONB table.
5. Per-table CRUD service + router.
6. Update existing services to read from the new structured fields (vs. the legacy embedded JSONB).
7. Backfill: existing students have their data migrated into the new tables; provenance recorded.
8. Tests: schema migrations + per-table CRUD + consent enforcement.

**Done when:** spec §3 fields are representable; the major-specific catalog is wired for at least 3 disciplines (CS, Business, Health); consent.training enforced.

---

## 8. Phase 5 — Discovery completeness

**Goal:** the type-first search + constraint chip experience matches the spec. Structured chips, individually editable.

**Specs:** `10-discovery.md`.
**Gap items:** G-S3, G-AI6.
**Effort:** 4 days.

**Steps:**
1. New agent `DiscoveryQueryInterpreter` per `45` §11 + spec.
2. Frontend: replace the single NLP summary chip with a chip-per-constraint UI.
3. Each chip: edit-in-place editor (degree dropdown, location autocomplete, budget slider, etc.).
4. Removing a chip updates URL state + reruns search.
5. Confirm vs. spec: filters panel + chips coexist; chip removal = filter clear.
6. Tests + visual.

**Done when:** typing "MS in Computer Science in California under $50k" returns the right programs AND extracts three editable chips; removing one chip widens the result set live.

---

## 9. Phase 6 — Universal Profile expansion

**Goal:** Profile page has 13 tabs covering all 19 sections; completion meter per category; edit-first UX.

**Specs:** `08-universal-profile.md`.
**Gap items:** G-S1.
**Effort:** 4 days (after Phase 4 lands the schema).

**Steps per `08`.**

---

## 10. Phase 7 — Match dual-score wiring

**Goal:** Fitness + Confidence visible on every program card surface.

**Specs:** `09-program-match.md`, `11-detail-pages-program.md`, `13-saved-list.md`.
**Gap items:** G-S2.
**Effort:** 2 days.

**Steps:**
1. Update `ProgramCard`, `UniversityCard`, `SchoolCard` to render DualRing on `fitness_score` + `confidence_score`.
2. Replace `MatchRing` on program detail page.
3. Add Confidence column to compare table.
4. Replace RationalePopover trigger to use AI Rationale Popover pattern from `02-design-system.md` §6.
5. Tests + visual.

**Done when:** legacy `match_score`/`match_tier` no longer rendered anywhere except for the explicit Phase E deprecation marker in `SchoolDetailPage`.

---

## 11. Phase 8 — Applications & Workshops polish

**Goal:** `ApplicationDetailPage` Guardrails tab fully wired; Workshops legacy code deleted.

**Specs:** `15-applications.md`, `14-workshops.md`.
**Gap items:** G-S4, G-A5.
**Effort:** 3 days.

**Steps:**
1. Backend `POST /me/applications/:id/guardrail-scan`.
2. Frontend wire `setGuardrailResult` to scan response.
3. Persist intent + rationale to `applications.intent_picker` + `intent_rationale`.
4. Delete legacy `EssayWorkshopPage.tsx` + `ResumeWorkshopPage.tsx` once `ProfilePage` no longer lazy-loads them.
5. Tests.

---

## 12. Phase 9 — Saved list persistence

**Goal:** Priority survives refresh.

**Specs:** `13-saved-list.md`.
**Gap items:** G-S5.
**Effort:** 0.5 day.

**Steps:**
1. Add `priority` column to `saved_lists`.
2. `PATCH /me/saved/:programId` accepts priority.
3. Frontend persists on change.
4. Tests.

---

## 13. Phase 10 — Institution editors

**Goal:** Replace raw JSON textareas in ProgramEditorPage + SettingsPage with guided form-based editors.

**Specs:** `23-program-detail-page-institution.md`.
**Gap items:** G-I1.
**Effort:** 4 days.

---

## 14. Phase 11 — Fairness signal + auto-halt

**Goal:** Disparate-impact tracking per cohort × week; auto-halt at Δ > 0.20 for 2 weeks; dashboard visibility.

**Specs:** `46-data-rights-privacy.md`.
**Gap items:** G-I5, G-D4.
**Effort:** 5 days.

**Steps:**
1. `fairness_signals` table; weekly compute job.
2. Service: compute disparate-impact per protected category × cohort × week.
3. Auto-halt mechanism: when Δ > 0.20 for 2 consecutive weeks, set `programs.matching_halted=true`.
4. Dashboard panel in `/i/dashboard` + dedicated page.
5. Override workflow (audit-logged, requires institutional admin role).
6. Tests including G-T3.

---

## 15. Phase 12 — Authenticity risk + AI assistive expansion

**Goal:** Essay anti-AI-pattern flagging; AI reply drafter in student Inbox; expand institution-side AI drafts.

**Specs:** `37-ai-extensibility.md`, `45-ai-agents-claude.md`.
**Gap items:** G-AI4, G-AI7.
**Effort:** 5 days.

---

## 16. Phase 13 — Peers / Connect Stage 3a

**Goal:** Build Peers feature.

**Specs:** new `20-connect.md`.
**Gap items:** G-S7, G-D3.
**Effort:** 5 days.

---

## 17. Phase 14 — Deferred items

- Bedrock as third provider.
- Data residency per institution.
- Multi-institution staff users.
- Streaming for DiscoveryOrchestrator.
- Multi-channel notifications (SMS, push).
- Bias auto-halt override review workflow.

Reassess in Q3 2026 against Series A milestones.

---

## 18. Per-session prompt template

When kicking off a new session against this roadmap:

```
I'm continuing the UniPaith MVP build per /Users/leozhu/Desktop/工作/UniPAith/Spec/.
Working on Phase <N> — <name>.

Per /Users/leozhu/Desktop/工作/UniPAith/Spec/48-build-sequencing.md §<N>,
read the listed specs, run the pre-work checklist, and implement the
phase's steps. Stop after Step <K> to confirm before moving to Step <K+1>.

Spec docs to load first:
- 00-overview.md
- 01-brand-tokens.md
- 02-design-system.md
- 04-llm-claude-migration.md
- 05-information-architecture.md
- <phase-specific spec docs>
- 47-current-vs-spec-gap-audit.md
- 48-build-sequencing.md
```

The session will:
1. Ask for prior-session context (CLAUDE.md session-continuity rule).
2. Run the pre-work checklist.
3. Read the spec docs.
4. Execute phase steps with TaskCreate tracking.
5. Open a PR per phase.

---

## 19. Dependency graph

```
Phase 1 (Brand)            ──────────────┐
Phase 2 (Claude)           ──────────────┼─→ Phase 4 ─→ Phase 6, 7, 8, 11, 12
Phase 3 (Cleanup)          ──────────────┘
Phase 4 (Data spine)       ─→ Phase 6, 7, 8, 11, 12
Phase 5 (Discovery)        ─→ Phase 7
Phase 6 (Profile)          ─→ Phase 8
Phase 7 (DualRing)         ─→ Phase 8
Phase 8 (Apps + Workshops) ─→ Phase 11
Phase 9 (Saved)            ─→ Phase 8 (priority feeds checklist)
Phase 10 (Editors)         ─→ Phase 11 (guided editors for fairness override)
Phase 11 (Fairness)        ─→ Phase 14
Phase 12 (AI Assistive)    ─→ Phase 14
Phase 13 (Peers)           ─→ Phase 14
```

---

## 20. Risk register

### Roadmap ordering tension (founder vs as-built)

Per `Misc./Roadmap.docx`, the founder sequences **Program Match before Discovery upgrade**, and **conversational/AI intake LAST (Phase 7)**. The shipped MVP leads with an **LLM-led Discover chat at `/s`** — the inverse. This spec set's phasing (§2) assumes chat-first stays (matches the shipped IA + `CLAUDE.md`). If the founder prefers the original sequence, Phases 5–6 (Discovery, Profile) would precede the chat polish. **Decision needed** — see `49-feature-backlog.md` §6.

### Risk register

| Risk | Mitigation |
|---|---|
| Europa Typekit kit not on company account / domain not allowlisted | Verify kit `spe3ioy` ownership + allowlist in Phase 1; system-ui fallback renders in-proportion meanwhile. `01` §10. |
| Claude API quota/limit | `/health/ai` probe + provider failover to OpenAI per `04` §9. |
| Schema migration breaks existing data | Run each migration first against staging dump; rollback playbook per phase. |
| Workshops generation-leak regression | The schema-enforced no-generation test (`test_workshop_no_generation_contract.py`) IS the contract; never weaken. |
| Fairness threshold false positives | Manual override workflow with audit log; threshold tunable per program in `programs.fairness_threshold_override`. |
| Institution data residency demand mid-sales-cycle | Defer feature; offer regional Bedrock pilot in Phase 14 if commercially required. |
