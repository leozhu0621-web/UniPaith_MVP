# Uni Guided Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename `/s` Discover→Uni and reshape it into a guided, stage-led AI workspace (left rail journey + living profile, center stage-by-stage conversation, inline first-look at matches), per `docs/superpowers/specs/2026-06-08-uni-guided-redesign-design.md`.

**Architecture:** Reuse-heavy. The unified `track="discovery"` session, extractor, validators, `completion_breakdown` ({profile,goals,needs}), and `OrchestratorResponse.suggested_options` already exist. New work: a stage-aware orchestrator state header (behind `ai_uni_guided_v1`), a two-pane frontend shell with a `JourneyRail` driven by `getCompletionMap()`, evolving `MatchHandoffCard`→`FirstLookCard` (reusing `getMatches`/`DualRing`), and the rename. No migration.

**Tech Stack:** FastAPI/SQLAlchemy (Python 3.12), React 19 + TS + Vite + Tailwind + TanStack Query + Zustand. Worktree `/tmp/wt-uni-guided`, branch `claude/uni-guided-redesign-8bf9e6`.

**Test lessons baked in (from #328):** every router-using component is wrapped in `MemoryRouter` in its test; `src/test/setup.ts` already stubs `apiClient.defaults.adapter` so unmocked calls reject synchronously; run `npx tsc -b` + `npx vite build` (not just vitest) before claiming green.

---

## Phase 0 — Rename (flag-independent, ships immediately)

### Task 1: Discover → Uni across labels

**Files:**
- Modify: `frontend/src/components/layout/StudentLayout.tsx` (NAV_ITEMS label)
- Modify: `frontend/src/components/layout/StudentTitle.tsx` (ROUTE_TITLES '/s')
- Modify: `frontend/src/components/student/GlobalSearch.tsx` (QUICK_NAV label + sub)
- Modify: `frontend/src/pages/student/OnboardingPage.tsx` (STAGES title)
- Modify: `frontend/src/pages/student/match/StrategyView.tsx` (copy + button)
- Modify: `frontend/src/pages/student/match/MatchesSection.tsx` (copy + button)
- Modify: `frontend/src/pages/student/DiscoverHomePage.tsx` (eyebrow)
- Test: `frontend/src/test/rename-uni.test.tsx` (new)

- [ ] **Step 1: Failing test** — assert nav + title show "Uni", not "Discover".

```tsx
// frontend/src/test/rename-uni.test.tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ROUTE_TITLES } from '../components/layout/StudentTitle'

describe('Discover → Uni rename', () => {
  it('routes /s to the "Uni" title', () => {
    expect(ROUTE_TITLES['/s']).toBe('Uni')
    expect(JSON.stringify(ROUTE_TITLES)).not.toMatch(/Discover/)
  })
})
```

- [ ] **Step 2: Run → FAIL** (`ROUTE_TITLES` not exported / still "Discover").

Run: `cd frontend && npx vitest run src/test/rename-uni.test.tsx`

- [ ] **Step 3: Implement the renames.**
  - `StudentLayout.tsx`: NAV_ITEMS `label: 'Discover'` → `label: 'Uni'` (keep `to: '/s'`, `icon: Compass`). Rename local `isDiscoverTab`→`isUniTab` if present (mechanical).
  - `StudentTitle.tsx`: `export const ROUTE_TITLES` (add `export` if missing); `'/s': 'Discover'` → `'/s': 'Uni'`.
  - `GlobalSearch.tsx`: QUICK_NAV `{ label: 'Discover', sub: 'Build your profile' }` → `{ label: 'Uni', sub: 'Build your profile with Uni' }`.
  - `OnboardingPage.tsx`: STAGES `title: 'Discover'` → `title: 'Meet Uni'`.
  - `StrategyView.tsx`: "build in Discover" → "build with Uni"; button `Open Discover` → `Talk to Uni`.
  - `MatchesSection.tsx`: "on Discover" → "with Uni"; button `Open Discover` → `Talk to Uni`.
  - `DiscoverHomePage.tsx`: eyebrow `Discover · with Uni` → `Uni`.
  - Leave `FinancialAidPage`/`CalendarPage` "Discover programs" CTAs (they mean browse programs, not the surface).

- [ ] **Step 4: Run → PASS** + `npx tsc -b`. Grep no stray nav "Discover": `grep -rn "Open Discover\|label: 'Discover'\|'/s': 'Discover'" src/` returns nothing.

- [ ] **Step 5: Commit** `feat(uni): rename Discover surface to Uni across nav/IA`.

---

## Phase 1 — Stage-aware orchestrator (behind `ai_uni_guided_v1`)

### Task 2: Add the feature flag

**Files:** Modify `unipaith-backend/src/unipaith/config.py`; modify `infra/ecs.tf` (env block, prod-on later).

- [ ] **Step 1:** Add to `config.py` near the other `ai_*` flags:

```python
# Uni guided redesign — when True, the discovery orchestrator leads the
# unified conversation stage-by-stage (current Discovery layer derived from
# completion_breakdown, narrated transitions, earned "continue"). When False
# (default), the open-ended unified Uni behavior is used. Frontend reads the
# same flag via /me (or ships the guided shell independently). Flip per-env.
ai_uni_guided_v1: bool = False
```

- [ ] **Step 2:** Verify import: `cd unipaith-backend && PYTHONPATH=src python -c "from unipaith.config import settings; print(settings.ai_uni_guided_v1)"` → `False`.
- [ ] **Step 3: Commit** `feat(uni): add ai_uni_guided_v1 flag`.

### Task 3: Stage-aware discovery state header

**Files:**
- Create: `unipaith-backend/src/unipaith/ai/journey.py` (pure stage helper)
- Modify: `unipaith-backend/src/unipaith/ai/orchestrator.py` (`_render_state_header` discovery branch)
- Test: `unipaith-backend/tests/test_uni_journey.py` (new)

The current stage = first of `["profile","goals","needs"]` whose completion < `HANDOFF_THRESHOLD` (0.5); if all ≥ threshold → `None` (ready for matches). The header tells Uni to lead that stage, and—if the just-prior turn moved a stage to ready—to narrate the transition.

- [ ] **Step 1: Failing test:**

```python
# unipaith-backend/tests/test_uni_journey.py
from unipaith.ai.journey import current_stage, STAGES

def test_current_stage_is_first_incomplete():
    assert current_stage({"profile": 0.8, "goals": 0.2, "needs": 0.0}) == "goals"

def test_current_stage_none_when_all_ready():
    assert current_stage({"profile": 0.6, "goals": 0.7, "needs": 0.9}) is None

def test_stages_order():
    assert STAGES == ("profile", "goals", "needs")
```

- [ ] **Step 2: Run → FAIL** (`unipaith.ai.journey` missing).

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_journey.py -v`

- [ ] **Step 3: Implement `journey.py`:**

```python
"""Uni guided-journey helpers — pure, deterministic stage math."""
from __future__ import annotations

STAGES: tuple[str, ...] = ("profile", "goals", "needs")
_LABELS = {"profile": "About you", "goals": "your goals", "needs": "what you need"}
_READY = 0.5  # mirrors discovery_service.HANDOFF_THRESHOLD


def current_stage(breakdown: dict[str, float]) -> str | None:
    """First Discovery layer not yet at the ready threshold, or None if all are."""
    for s in STAGES:
        if float(breakdown.get(s, 0.0)) < _READY:
            return s
    return None


def stage_label(stage: str | None) -> str:
    return _LABELS.get(stage or "", "your matches")
```

- [ ] **Step 4:** In `orchestrator.py`, give `TurnContext` a `completion_breakdown: dict | None = None` field (if not present) and rewrite the `if ctx.track == "discovery":` branch of `_render_state_header` to be stage-aware **only when guided** (gate with a `ctx.guided: bool` flag threaded from the service; when not guided, keep the existing open text verbatim as fallback):

```python
if ctx.track == "discovery":
    from unipaith.ai.journey import current_stage, stage_label
    if not getattr(ctx, "guided", False):
        return (  # unchanged open-discovery fallback
            "## Current state\n\n"
            "You are in one open discovery conversation with this student. "
            "There are no tracks to pick — explore whatever they open up, and over "
            "time naturally cover who they are, what they want, and what they need.\n"
            f"- Completion so far: {ctx.completion_pct:.0%}\n"
            f"- Still useful to learn: {missing}\n"
            f"- A possible next probe: {next_probe}\n\n"
            "## What we already know about this student\n\n"
            f"{ctx.known_profile_summary or '(nothing yet)'}\n\n"
            "## Recently captured signals (this session)\n\n"
            f"{ctx.recent_signals_summary or '(none yet)'}"
        )
    bd = ctx.completion_breakdown or {}
    stage = current_stage(bd)
    focus = (
        f"You are guiding this student through a stage: **{stage_label(stage)}**. "
        "Lead this stage — ask about it, one question at a time, offering 2-3 short "
        "tappable options via `suggest_replies`. When this stage has enough signal, "
        "warmly say so and offer to move on (do not force it)."
        if stage else
        "You've learned enough across who they are, their goals, and their needs. "
        "Warmly tell them you're ready to show a first look at matches."
    )
    return (
        "## Current state\n\n"
        f"{focus}\n"
        f"- Stage coverage — about you {bd.get('profile',0):.0%}, "
        f"goals {bd.get('goals',0):.0%}, needs {bd.get('needs',0):.0%}\n"
        f"- A possible next probe: {next_probe}\n\n"
        "## What we already know about this student\n\n"
        f"{ctx.known_profile_summary or '(nothing yet)'}\n\n"
        "## Recently captured signals (this session)\n\n"
        f"{ctx.recent_signals_summary or '(none yet)'}"
    )
```

- [ ] **Step 5:** Thread `guided` + `completion_breakdown` into `TurnContext` where the service builds it (both `append_message` `_run_v2_turn` and `stream_message`): set `guided=settings.ai_uni_guided_v1` and `completion_breakdown=session.completion_breakdown or {}`. (Read `from unipaith.config import settings`.)

- [ ] **Step 6: Run → PASS** (journey tests) + full discovery/orchestrator suite:

Run: `cd unipaith-backend && PYTHONPATH=src DATABASE_URL=... COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true .venv/bin/pytest tests/ -q -k "discovery or orchestrator or uni_journey or uni_eval" ; echo EXIT=$?`
Expected: all pass (fallback path unchanged when flag off).

- [ ] **Step 7: Commit** `feat(uni): stage-aware discovery orchestrator behind ai_uni_guided_v1`.

### Task 4: Extend the Uni eval for stage-leading

**Files:** Modify `unipaith-backend/src/unipaith/ai/evals/uni_counselor.py`; modify `unipaith-backend/tests/test_uni_eval.py`.

- [ ] **Step 1: Failing test** — a stage-leading turn that asks about the current stage + offers options passes; one that ignores the stage flags `off_stage`.

```python
def test_eval_flags_off_stage_turn():
    from unipaith.ai.evals.uni_counselor import score_stage_turn
    r = score_stage_turn(stage="goals", assistant="What's your favorite color?")
    assert not r.passed and "off_stage" in r.reasons

def test_eval_passes_on_stage_turn():
    from unipaith.ai.evals.uni_counselor import score_stage_turn
    r = score_stage_turn(stage="goals",
        assistant="When you picture life after college — a career, a field, or still open?")
    assert r.passed
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** `score_stage_turn(stage, assistant)` in `uni_counselor.py` — deterministic: a stage has keyword sets (`goals`→{career, field, after college, want, future, dream}; `needs`→{afford, money, aid, location, near, support, distance}; `profile`→{you, enjoy, love, class, value, who}); pass if `_question_count(assistant) >= 1` and any stage keyword appears (case-insensitive); else `off_stage`. Reuse `CounselorVerdict`.
- [ ] **Step 4: Run → PASS.**
- [ ] **Step 5: Commit** `test(uni): stage-leading eval check`.

---

## Phase 2 — Frontend workspace shell + rail

### Task 5: `useJourneyState` hook

**Files:** Create `frontend/src/pages/student/discover/useJourneyState.ts`; test `frontend/src/test/use-journey-state.test.tsx`.

Derives the journey model from `getCompletionMap()` + `getHandoffVerdict()`.

- [ ] **Step 1: Failing test:**

```tsx
// frontend/src/test/use-journey-state.test.tsx
import { describe, it, expect } from 'vitest'
import { deriveStages } from '../pages/student/discover/useJourneyState'

describe('deriveStages', () => {
  it('marks first incomplete as current, prior as done, later as locked', () => {
    const s = deriveStages({ profile: '0.8', goals: '0.2', needs: '0' })
    expect(s.map(x => [x.key, x.state])).toEqual([
      ['profile', 'done'], ['goals', 'current'], ['needs', 'locked'],
    ])
  })
  it('all done unlocks matches', () => {
    const s = deriveStages({ profile: '0.6', goals: '0.7', needs: '0.9' })
    expect(s.every(x => x.state === 'done')).toBe(true)
  })
})
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** `useJourneyState.ts`:

```tsx
import { useQuery } from '@tanstack/react-query'
import { getCompletionMap, getHandoffVerdict } from '../../../api/discovery'
import type { CompletionMap, HandoffVerdict } from '../../../types'

export type StageKey = 'profile' | 'goals' | 'needs'
export type StageState = 'done' | 'current' | 'locked'
export interface JourneyStage { key: StageKey; label: string; state: StageState; pct: number }

const READY = 0.5
const LABELS: Record<StageKey, string> = { profile: 'About you', goals: 'Your goals', needs: 'What you need' }
const ORDER: StageKey[] = ['profile', 'goals', 'needs']

export function deriveStages(c: Partial<CompletionMap> | undefined): JourneyStage[] {
  const pct = (k: StageKey) => Number(c?.[k] ?? 0)
  const firstIncomplete = ORDER.find(k => pct(k) < READY)
  return ORDER.map(key => {
    const p = pct(key)
    const state: StageState = p >= READY ? 'done' : key === firstIncomplete ? 'current' : 'locked'
    return { key, label: LABELS[key], state, pct: p }
  })
}

export function useJourneyState(enabled: boolean) {
  const { data: completion } = useQuery<CompletionMap>({
    queryKey: ['discovery', 'completion'], queryFn: getCompletionMap, enabled,
  })
  const { data: handoff } = useQuery<HandoffVerdict>({
    queryKey: ['discovery', 'handoff'], queryFn: getHandoffVerdict, enabled,
  })
  const stages = deriveStages(completion)
  const currentStage = stages.find(s => s.state === 'current') ?? null
  const matchesUnlocked = !!handoff?.should_handoff
  return { stages, currentStage, matchesUnlocked, completion }
}
```

- [ ] **Step 4: Run → PASS** + `npx tsc -b`.
- [ ] **Step 5: Commit** `feat(uni): useJourneyState derives stages from completion map`.

### Task 6: `JourneyRail` component

**Files:** Create `frontend/src/pages/student/discover/JourneyRail.tsx`; test `frontend/src/test/journey-rail.test.tsx`.

Renders: "Stage 01 · Discovery" + the three stages (✓done / ◉current / lock-locked, click `done`→`onRevisit(key)`), a "Stage 02 · a first look" item ("Your matches" — unlocked or "unlocks once Uni knows enough"), and the living-profile panel (reuse `ProfileDrawer`'s grouped chips logic — extract a shared `LivingProfilePanel` from ProfileDrawer's body so rail + drawer share it). Props: `{ stages, matchesUnlocked, onRevisit(key), onOpenMatches, livingProfile, onAsk }`.

- [ ] **Step 1: Failing test** — renders the 3 stage labels + "Your matches"; a done stage triggers `onRevisit`; matches-locked shows the locked copy. Wrap in `MemoryRouter` + `QueryClientProvider`; mock `../api/livingProfile`.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** `JourneyRail.tsx` + extract `LivingProfilePanel.tsx` from `ProfileDrawer` (move the narrative + 3 grouped editable-chip sections + gap invitations + "View full profile →" into `LivingProfilePanel({ data, onAsk, onClose? })`; `ProfileDrawer` renders `<LivingProfilePanel/>` inside its `Sheet`; the rail renders it inline). Follow existing Tailwind tokens (`text-eyebrow`, `bg-card`, `border-border`, `text-secondary`). Editable chips reuse `EditableChip` from `NoticedCard`.
- [ ] **Step 4: Run → PASS** + `npx tsc -b`.
- [ ] **Step 5: Commit** `feat(uni): JourneyRail + shared LivingProfilePanel`.

### Task 7: Two-pane shell + mobile

**Files:** Modify `frontend/src/pages/student/DiscoverHomePage.tsx`; modify `frontend/src/test/discover-home.test.tsx`.

Desktop (≥ lg): two columns — `<JourneyRail/>` (w-64 left) + `<UniConversation/>` (flex-1). Mobile (< lg): single column with a slim top **journey bar** (current stage + dot progress, tap → opens a bottom `Sheet` holding `<JourneyRail/>`); conversation below. Gate the whole guided shell on a frontend flag read (see Task 8 note) — when off, render the current single-column `<UniConversation/>` (no rail) so nothing regresses.

- [ ] **Step 1: Failing test** — on a wide viewport mock, the rail's "Your goals" + the conversation both render; tapping a done stage calls into the conversation revisit. Extend `discover-home.test.tsx` (already mocks discovery + livingProfile; add `getCompletionMap`/`getHandoffVerdict` mocks).
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** the two-pane layout + mobile journey bar + Sheet(side="bottom"). `useJourneyState(guided)` feeds the rail; `onRevisit(key)` calls a new `UniConversation` imperative prop `onRevisitStage` (Task 8) that sends "Let's revisit <label>."
- [ ] **Step 4: Run → PASS** + `npx tsc -b` + `npx vite build`.
- [ ] **Step 5: Commit** `feat(uni): two-pane workspace shell + mobile journey bar`.

### Task 8: Stage header, progress, chips, Continue gate in `UniConversation`

**Files:** Modify `frontend/src/pages/student/discover/UniConversation.tsx`; modify `frontend/src/test/discover-home.test.tsx`.

- Add a **stage header** above the thread: current stage label + a progress bar from `useJourneyState`.
- Render **LLM chips**: read `suggested_options` off the latest assistant message's `extracted_signals` and render them as tappable chips (replacing the static `QUICK_REPLIES` when present; keep a "Uni, you suggest" affordance + the static set as fallback when empty).
- **Earned Continue:** when the current stage's `state` flips to `done` (or handoff ready), show a "Continue to <next>" button that sends a gentle "Let's move on to <next>." nudge (or scrolls to the unlocked first-look when all done).
- Accept `onRegisterRevisit?(fn)` / a `revisitSignal` prop so the rail can drive "revisit <stage>".
- Feature-flag read: add `getMe()`/auth-store `ai_uni_guided_v1` (if exposed) OR a simple `VITE`-independent prop `guided` passed from `DiscoverHomePage`; default the shell guided=true once shipped (the backend flag governs the *conversation* behavior; the shell is safe regardless).

- [ ] **Step 1: Failing test** — with a mocked session whose latest assistant message has `extracted_signals.suggested_options = ['A field','Still open']`, those chips render and clicking one calls `appendMessage`. Stage header shows "Your goals".
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** (read `detail.messages.at(-1)`; `const chips = (last?.role==='assistant' && Array.isArray(last.extracted_signals?.suggested_options)) ? last.extracted_signals.suggested_options : []`). Stage header from `useJourneyState`. Continue button logic.
- [ ] **Step 4: Run → PASS** + `npx tsc -b` + `npx vite build`.
- [ ] **Step 5: Commit** `feat(uni): stage header, LLM chips, earned Continue`.

---

## Phase 3 — Inline first look

### Task 9: `FirstLookCard` (evolve `MatchHandoffCard`)

**Files:** Modify `frontend/src/pages/student/discover/MatchHandoffCard.tsx` → rename to `FirstLookCard.tsx` (keep a thin `MatchHandoffCard` re-export if other importers exist; grep first); update `UniConversation.tsx` import; test `frontend/src/test/first-look-card.test.tsx`.

When `should_handoff`, fetch top matches and render: recap line + top **3** rows (program name + `<DualRing fitness confidence compact/>` + one-line `rationale_text` or band) + honest note + "Go deeper in Match →" (`navigate('/s/explore')`) + "Keep talking." Uses `getMatches(false)` from `api/matching`, takes `.slice(0,3)`. Degrade: if matches empty/error, show recap + go-deeper only.

- [ ] **Step 1: Failing test** — given `getMatches` mocked with 3 `MatchResultDual`, the card shows all 3 program names + a "Go deeper in Match" button that navigates to `/s/explore`. Wrap in `MemoryRouter` (Routes `/s/explore` → "EXPLORE") + `QueryClientProvider`; mock `../api/matching` + `../api/discovery`.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** `FirstLookCard.tsx` (reuse `DualRing` from `../match/DualRing`, `Number(m.fitness_score)`/`Number(m.confidence_score)`). Keep the `variant`/`onKeepTalking` props. `UniConversation` renders `<FirstLookCard variant="auto" .../>` when `matchesUnlocked`.
- [ ] **Step 4: Run → PASS** + `npx tsc -b` + `npx vite build`.
- [ ] **Step 5: Commit** `feat(uni): inline FirstLookCard with top-3 dual-score matches`.

---

## Phase 4 — Verify & ship

### Task 10: Regression, flags, fallback, ship

- [ ] **Step 1: Backend** — `cd unipaith-backend && PYTHONPATH=src DATABASE_URL=... COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true .venv/bin/pytest tests/ -q -k "discovery or orchestrator or uni_ or plan2 or match" ; echo EXIT=$?` — all pass; confirm flag-off fallback path + `test_plan2_integration` + `test_workshop_no_generation_contract` green. `ruff check src tests`.
- [ ] **Step 2: Frontend** — `cd frontend && npx vitest run ; npx tsc -b ; npx vite build ; npx eslint src/pages/student/discover src/components/layout` — all green (231+ tests + new).
- [ ] **Step 3:** Set `ai_uni_guided_v1 = "true"` in `infra/ecs.tf` env block (prod-on, per standing practice) — additive.
- [ ] **Step 4: Commit** any fixes; push branch; open PR; drive CI green → squash-merge → watch deploy; verify live bundle (`grep` nav "Uni", the rail, "first look").

---

## Self-Review

**Spec coverage:** §1–§3 rename → Task 1; journey/stages → Tasks 3,5,6; §4 guided mechanics (stage intro/chips/Continue/transitions/revisit) → Tasks 3,7,8; §5 first-look → Task 9; §6 rail+mobile → Tasks 6,7; §7 architecture (flag, no migration, reuse) → Tasks 2,3,5,6,9; §9 fallback → Task 3 (flag-off branch) + Task 10; §10 rollout → Tasks 2,10; §11 testing → every task + Task 10. LLM chips already exist (`suggested_options`) → rendered in Task 8 (no new agent). No gaps.

**Placeholder scan:** code shown for the novel logic (journey.py, useJourneyState, orchestrator header, eval, key tests); routine Tailwind markup follows existing components (NoticedCard/ProfileDrawer/DualRing) by explicit reference. No TBD/TODO.

**Type consistency:** `StageKey`/`StageState`/`JourneyStage`, `deriveStages`, `useJourneyState`, `current_stage`/`STAGES`/`stage_label`, `score_stage_turn`, `FirstLookCard`, `LivingProfilePanel` used consistently across tasks. `completion_breakdown` keys = `{profile,goals,needs}`; `CompletionMap` adds `identity` (rail ignores it). `suggested_options` is the existing field name (not `suggested_replies`) — the spec's "suggested_replies" maps to the live `suggested_options`.

## Notes for the executor
- Work on `claude/uni-guided-redesign-8bf9e6` in `/tmp/wt-uni-guided`. Symlink `frontend/node_modules` + backend `.venv` from a sibling worktree; copy `.env`. Coordinate (`git fetch origin main` + merge) before pushing — Discover/types/test-list are hot files.
- Per the project owner: implementation + online deploy proceed autonomously after this plan (no further per-step approval).
