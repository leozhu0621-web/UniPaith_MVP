# My Space ↔ Chat strategy lineup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use `- [ ]`.

**Goal:** Make the My Space Strategy tab line up with the new Chat tab — reframe it to the white-paper "angle → school list (fit/odds)" model, hand off to the chat's real template, and link the chat's strategy artifact back to My Space.

**Architecture:** Reuse existing data — the chat's `generate_strategy` action is ALREADY real (`api/chat_sessions.py` `_REAL_ACTIONS` → `tool_generate_strategy` → `StrategyService.generate` → the one active `StudentStrategy`). My Space reads the same `StudentStrategy` (`['strategy','active']`) + `getMatches()` (`['matches']`). So this is presentation + two small wires, no new ML, no new strategy model.

**Tech Stack:** React 19 / TS / Vite / TanStack Query (frontend) · FastAPI / Pydantic (backend).

Spec: `docs/superpowers/specs/2026-06-20-myspace-chat-strategy-lineup-design.md`.

---

### Task 1 — Strategy tab → white-paper framing (frontend; the bulk)

**Files:**
- Create: `frontend/src/pages/student/profile/strategy/scoreWords.ts` — `fitWord`/`oddsWord` helpers.
- Create: `frontend/src/pages/student/profile/strategy/SchoolList.tsx` — the recommended-list section.
- Modify: `frontend/src/pages/student/profile/StrategyTab.tsx` — reframe to angle + school list; keep `<PlanOverview/>` + the generate/develop actions + drafts.
- Test: `frontend/src/test/strategy-scorewords.test.ts`.

- [ ] `scoreWords.ts`: `fitWord(score: number|null): string` from `fitness_score` (≥.85 Excellent · ≥.7 Strong · ≥.55 Good · ≥.4 Moderate · else Low) returning `"<word> fit"`; `oddsWord(score: number|null): string` from the admission-likelihood proxy `confidence_score` (≥.8 Safe · ≥.6 Likely · ≥.4 Toss-up · ≥.2 Reach · else Long shot). Both clamp/guard null → return `null` (no tag). Unit-test the boundaries.
- [ ] `SchoolList.tsx`: `useQuery(['matches'], getMatches)`; render the top ~6 `MatchResultDual` as cards — name/program, a **Fitness** tag (cobalt: `bg-background-info`-style `bg-secondary/10 text-secondary`) + an **Odds** tag (neutral/`bg-muted`), a one-line reason if present, and a "See all matches in Discover" link to `/s/explore`. No bars/tables. Self-hides (renders a calm empty line) when no matches. Semantic tokens, dark-safe.
- [ ] `StrategyTab.tsx`: lead the active-strategy block with **"Your angle"** — `career_target → target_degree` + the `narrative`, with the academic/financial/geographic paths demoted to supporting chips/detail (keep the data, not the headline). Render `<SchoolList/>` below the angle. Keep `<PlanOverview/>`, the Generate/Develop buttons, and drafts. Use the shared `fitWord`/`oddsWord`.
- [ ] Verify: `cd frontend && npx tsc -p tsconfig.app.json --noEmit` (0) · `npx vitest run` (green) · `npx eslint <changed>` (0 err) · `npm run build` (0).
- [ ] Commit.

### Task 2 — Handoff: "Develop with Uni" launches the template (frontend)

**Files:**
- Modify: `frontend/src/pages/student/profile/StrategyTab.tsx` — the "Develop with Uni" onClick.
- Modify: `frontend/src/pages/student/chat/ChatTabShell.tsx` — accept `?session=<id>` to open a session active (read it; if absent behave as today).

- [ ] StrategyTab "Develop with Uni": replace `navigate('/s?intent=strategy')` with: `const s = await createSession({ title: 'Sharpen your strategy', topic_key: 'strategy', origin_kind: 'template', origin_ref: 'sharpen_strategy' }); navigate('/s?session=' + s.id)`. (`createSession` from `api/chatSessions`.) Use a mutation; disable while pending; on error show a toast and fall back to `navigate('/s')`.
- [ ] ChatTabShell: read `?session=` (useSearchParams) once on mount and set it as the active session (it already routes `originKind === 'template' && originRef` → `<TemplateRunner templateKey={originRef}/>`). If the param is missing, unchanged.
- [ ] Verify (tsc/eslint/vitest/build, as Task 1). Commit.

### Task 3 — A-link: chat strategy artifact → My Space (full-stack, small)

**Files:**
- Modify: `unipaith-backend/src/unipaith/api/chat_sessions.py` — `ActionArtifactOut` + the `generate_strategy` branch.
- Modify: `frontend/src/api/chatTemplates.ts` — `ActionArtifact` type.
- Modify: `frontend/src/pages/student/chat/TemplateRunner.tsx` — `ActionArtifactCard` renders the link.
- Test: `unipaith-backend/tests/test_chat_actions.py` (extend if present, else add).

- [ ] Backend: add `link: str | None = None` to `ActionArtifactOut`; in the `generate_strategy` branch set `link="/s/profile?tab=strategy"` on the returned artifact. (build_school_list/compare_schools may set `link="/s/explore"` — optional, same task.)
- [ ] Backend test: `dispatch_template_action('generate_strategy')` returns `status` and (when ready) `link == "/s/profile?tab=strategy"`; unknown key → 400; a non-real action (e.g. `find_events`) → `status=="pending"`, `link is None`.
- [ ] Frontend: `ActionArtifact` gains `link?: string | null`; `ActionArtifactCard` renders a trailing "Open in My Space →" link (uses react-router `Link`/navigate) when `artifact.link` is set.
- [ ] Verify backend (ast/ruff/targeted pytest via CI — no local venv in worktree; reuse main's venv if available) + frontend (tsc/eslint/vitest/build). Commit.

### Final
- [ ] Mock-user verification (preview recipe in memory `project_profile_refinement_v2`): on the reframed Strategy tab, the angle + school list with separate fit/odds tags render; "Develop with Uni" opens the Sharpen-your-strategy runner; running it produces a real strategy that appears on the tab; the artifact card links back.
- [ ] Ship via `/ship` (single alembic head — no migration here; backend change is additive). Confirm live.

## Self-review
- Spec coverage: Part A (already-real generate_strategy) → Task 3 adds the My Space link (the only A-gap). Part B → Task 2. Part C → Task 1. Phase 2 (other actions) is explicitly out of this plan.
- No placeholders: each task names exact files + the concrete change; the one judgment call (odds = `confidence_score` proxy) is stated.
- Type consistency: `fitWord`/`oddsWord` defined in Task 1 and reused; `ActionArtifactOut.link` (backend) ↔ `ActionArtifact.link` (frontend) match in Task 3.
