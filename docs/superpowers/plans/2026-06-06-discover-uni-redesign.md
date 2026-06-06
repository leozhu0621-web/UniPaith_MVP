# Discover "Uni" Counselor Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild Discover as one warm, single-column conversation with "Uni" (a real college counselor) plus a quiet editable living profile, replacing the track-tabbed interrogation UI — while keeping the data model, matching, and strategy flow unchanged.

**Architecture:** Backend keeps the discovery tables, extractor, matching, flags, and rule-based fallback. We (a) give the orchestrator a Uni counselor system prompt + always/never playbook, (b) decouple signal extraction from `session.track` so one conversation feeds goals+needs+identity, and (c) surface readiness as Uni's offer. Frontend replaces `DiscoverHomePage`/`ChatPanel` with a single-column Uni conversation (inline editable "Noticed" cards, a living-profile slide-over, an in-thread match handoff). Uni's playbook also becomes a constitution + eval set.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2 async / Anthropic SDK (backend); React 19 / TS / Vite / TanStack Query / Tailwind (frontend); pytest + vitest.

**Branch:** `claude/discover-uni-redesign-8bf9e6` (off latest `origin/main`). Spec: `docs/superpowers/specs/2026-06-06-discover-uni-conversation-redesign-design.md`.

**Conventions:** backend tests `cd unipaith-backend && DATABASE_URL=… PYTHONPATH=src AI_MOCK_MODE=true COGNITO_BYPASS=true S3_LOCAL_MODE=true .venv/bin/pytest <file> -q`; use an isolated DB (parallel sessions share the box). Frontend `cd frontend && npx vitest run <file>` + `npx tsc --noEmit`. Commit after every green step. Never bypass hooks.

---

## File Structure

**Backend (`unipaith-backend/src/unipaith/`)**
- `ai/prompts/_shared/uni_counselor.md` — **new**. Uni persona + always/never counselor playbook. Concatenated into the discovery system prompt.
- `ai/prompts/orchestrator_discovery.md` — **modify**. Reference Uni; support a track-less "discovery" mode; one-question-per-turn, reflect-then-ask.
- `ai/orchestrator.py` — **modify**. Include `uni_counselor.md`; `_render_state_header` tolerates `track="discovery"`; expose persona name.
- `services/discovery_service.py` — **modify**. Content-routed validation/extraction: when `session.track == "discovery"`, run the basic + goals + needs (+ identity gate) validators every turn so one conversation populates all signal stores. Add `start_unified_session`. Keep legacy track behavior intact.
- `models/discovery.py` — **modify** (if a CHECK constraint restricts `track`): allow `"discovery"`.
- `alembic/versions/<rev>_discovery_unified_track.py` — **new** (only if the CHECK needs widening).
- `ai/evals/fixtures/uni/*.json` — **new**. Uni counselor eval fixtures.
- `ai/evals/uni_counselor.py` — **new**. Deterministic structural eval (one-question, no-slang, reflection present) wired into the eval registry.

**Frontend (`frontend/src/`)**
- `pages/student/DiscoverHomePage.tsx` — **rewrite** to single column (Uni header + conversation + "✦ Your profile" trigger). Remove TrackSelector/LayerSwitcher/StrategyHandoffCTA/rails.
- `pages/student/discover/UniConversation.tsx` — **new** (replaces ChatPanel's role). Bubbles, opener, one-at-a-time, counselor quick-replies, composer, streaming dots.
- `pages/student/discover/NoticedCard.tsx` — **new**. Inline editable confirmation card.
- `pages/student/discover/ProfileDrawer.tsx` — **new**. Living-profile slide-over (narrative + editable chips + gap invitations).
- `pages/student/discover/MatchHandoffCard.tsx` — **new**. In-thread "See programs that fit me" card.
- `api/discovery.ts` — **modify**. `startUnifiedSession`, `updateSignal` (edit inference), `getLivingProfile`.
- Deleted from Discover use: `discover/TrackSelector.tsx`, `discover/ReadinessRail.tsx`, `discover/ArtifactRail.tsx` (keep files if Profile page imports them; otherwise remove imports only).

---

## Phase A — Backend: Uni the counselor

### Task 1: Uni counselor playbook prompt + wire into the orchestrator

**Files:**
- Create: `unipaith-backend/src/unipaith/ai/prompts/_shared/uni_counselor.md`
- Modify: `unipaith-backend/src/unipaith/ai/orchestrator.py` (`_build_discovery_system_prompt`, ~line 67)
- Test: `unipaith-backend/tests/test_uni_orchestrator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_uni_orchestrator.py
from unipaith.ai.orchestrator import _DISCOVERY_SYSTEM_PROMPT

def test_system_prompt_includes_uni_playbook():
    p = _DISCOVERY_SYSTEM_PROMPT.lower()
    assert "uni" in p                      # persona named
    assert "one question" in p             # one-question-per-turn rule
    assert "reflect" in p                  # active listening
    assert "no slang" in p or "avoid slang" in p
```

- [ ] **Step 2: Run it — expect FAIL** (`uni_counselor.md` not yet concatenated)

Run: `… pytest tests/test_uni_orchestrator.py -q` → FAIL.

- [ ] **Step 3: Create `uni_counselor.md`** with the playbook from the spec §3.1–§3.2:

```markdown
# You are Uni — a real college counselor

You are **Uni**, a warm, professional college counselor guiding a student through
self-discovery. Your goal: help them find where they will genuinely thrive, not
just where they can get in.

## Voice
Warm, calm, composed, personal. Acknowledge before you ask. Use "we." NEVER use
slang, "lol," emoji-speak, or an over-familiar register. You are a trusted adult
professional, not a buddy.

## Always
- Build rapport and safety first; normalize "there are no wrong answers."
- Ask OPEN questions about CONCRETE moments ("when did you feel absorbed?"),
  not abstract traits ("are you analytical?").
- REFLECT the student's own words back before going deeper (active listening).
- VALIDATE and normalize feelings; never judge.
- Probe ONE layer at a time, then offer perspective/options like a counselor
  guiding — not just firing questions.
- SUMMARIZE and check ("So it sounds like…") and tie back to fit/thriving.

## Never
- Slang / "lol" / emoji-speak / over-familiar register.
- Interrogate (rapid-fire question→answer→question with no reflection).
- Ask MORE THAN ONE real question per turn.
- Judge, pressure, or use ranking/anxiety language.
```

- [ ] **Step 4: Concatenate it** in `orchestrator.py` `_build_discovery_system_prompt` — add after `_CONSTITUTION_TEXT` load:

```python
_UNI_TEXT = _load_prompt("_shared/uni_counselor.md")
# inside _build_discovery_system_prompt(): prepend Uni so persona frames everything
def _build_discovery_system_prompt() -> str:
    return "\n\n".join([_UNI_TEXT, _DISCOVERY_PROMPT_TEXT, _FRAMEWORKS_TEXT, _CONSTITUTION_TEXT])
```

- [ ] **Step 5: Run test — expect PASS.** Then `ruff check src tests`.

- [ ] **Step 6: Commit**

```bash
git add src/unipaith/ai/prompts/_shared/uni_counselor.md src/unipaith/ai/orchestrator.py tests/test_uni_orchestrator.py
git commit -m "feat(discover): Uni counselor playbook in the discovery system prompt"
```

### Task 2: Track-less "discovery" mode in the orchestrator

**Files:**
- Modify: `unipaith-backend/src/unipaith/ai/orchestrator.py` (`_render_state_header`, ~line 254)
- Test: `unipaith-backend/tests/test_uni_orchestrator.py`

- [ ] **Step 1: Failing test** — header renders for a unified session without leaking track jargon:

```python
from unipaith.ai.orchestrator import Orchestrator, TurnContext

def test_state_header_unified_discovery():
    ctx = TurnContext(track="discovery", layer=None, completion_pct=0,
                      cross_track_summary="", history=[])
    header = Orchestrator._render_state_header(ctx)
    assert "discovery" in header.lower()
    assert "Profile/Goals/Needs" not in header  # no track menu pushed at the model
```

- [ ] **Step 2: Run → FAIL** (header assumes a concrete track).

- [ ] **Step 3: Make `_render_state_header` tolerate `track="discovery"`** — when track is `discovery`, render a neutral "You are in an open discovery conversation; explore whatever the student opens up, covering their self, goals, and needs over time" instead of a single-track label. Keep existing branches for legacy tracks.

- [ ] **Step 4: Run → PASS.** `ruff check`.

- [ ] **Step 5: Commit** `feat(discover): orchestrator supports unified track-less discovery`.

### Task 3: Content-routed extraction (one conversation → goals+needs+identity)

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/discovery_service.py` (validation routing ~lines 287/301/675; add `start_unified_session`)
- Modify: `unipaith-backend/src/unipaith/models/discovery.py` (+ migration) only if `track` has a CHECK constraint excluding `"discovery"`
- Test: `unipaith-backend/tests/test_unified_discovery_extraction.py`

- [ ] **Step 1: Failing integration test** — a single unified session whose messages mention an interest, a goal, and a need produces rows in all three stores:

```python
@pytest.mark.asyncio
async def test_unified_session_populates_all_signal_stores(db_session, mock_student_user):
    svc = DiscoveryService(db_session)
    s = await svc.start_unified_session(mock_student_user.id)
    # AI_MOCK_MODE returns deterministic extracted_signals spanning types
    await svc.append_message(s.id, role="student",
        content="I love building robots. I want to be an engineer. I need financial aid.")
    snap = await svc.get_snapshot(mock_student_user.id)
    assert snap.goals and snap.needs and snap.identity_or_interests
```

- [ ] **Step 2: Run → FAIL** (`start_unified_session` missing; extraction track-gated).

- [ ] **Step 3: Add `start_unified_session`** (creates a session with `track="discovery"`, `layer=None`).

- [ ] **Step 4: Generalize the validation/extraction block** (~line 287): when `session.track == "discovery"`, run the basic validator + goals validator + needs validator (+ identity judge gate) on every turn, so signals route by content rather than by a fixed track. Keep the existing per-track branches for legacy sessions. Pseudocode:

```python
if session.track == "discovery":
    # run all extractors; each writes only the signals it finds
    default_validator.validate(layer="basic", snapshot=snapshot)
    default_validator.validate_track(track="goals", snapshot=snapshot)
    default_validator.validate_track(track="needs", snapshot=snapshot)
    # identity judge only when the basic gate is satisfied (token-thrifty)
    ...
    session.completion_pct = _unified_completion(snapshot)
elif session.track == "profile" and session.layer in {...}:
    ...  # unchanged legacy path
```

- [ ] **Step 5: If `track` is CHECK-constrained**, widen it: model + `make migration MSG="discovery unified track"`; re-point `down_revision` to the current single head (`alembic heads`). Additive only.

- [ ] **Step 6: Run test (isolated DB) → PASS.** Then run `tests/test_plan2_integration.py` to confirm fallback still never 5xxes.

- [ ] **Step 7: Commit** `feat(discover): content-routed extraction for unified Uni conversation`.

### Task 4: Uni constitution + eval

**Files:**
- Create: `unipaith-backend/src/unipaith/ai/evals/fixtures/uni/counselor_turns.json`
- Create: `unipaith-backend/src/unipaith/ai/evals/uni_counselor.py`
- Test: `unipaith-backend/tests/test_uni_eval.py`

- [ ] **Step 1: Failing test** — the eval flags a slangy / multi-question / no-reflection turn and passes a good counselor turn:

```python
from unipaith.ai.evals.uni_counselor import score_counselor_turn

def test_eval_flags_bad_turn():
    bad = "lol nice. what's your gpa? what's your major? where do you wanna go?"
    r = score_counselor_turn(prior_student="I liked bio", assistant=bad)
    assert not r.passed and ("slang" in r.reasons or "multiple_questions" in r.reasons)

def test_eval_passes_counselor_turn():
    good = ("It sounds like bio really drew you in. When you were in it, what "
            "part made you lose track of time?")
    r = score_counselor_turn(prior_student="I liked bio", assistant=good)
    assert r.passed
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement `score_counselor_turn`** — deterministic structural checks: count `?` (>1 → `multiple_questions`); slang lexicon (`lol`, `omg`, emoji) → `slang`; reflection heuristic (overlap with prior student words OR an acknowledgment phrase) → else `no_reflection`. Return `(passed, reasons)`.

- [ ] **Step 4: Add fixtures** (5–8 good + bad counselor turns) and register the suite in the eval runner (mirror `ai/evals/constitution.py`). These gate deterministically in CI (no API key).

- [ ] **Step 5: Run → PASS.** `ruff check`.

- [ ] **Step 6: Commit** `feat(discover): Uni counselor eval (one-question, no-slang, reflection)`.

---

## Phase B — Frontend: the Uni conversation

### Task 5: Single-column Discover + Uni conversation shell

**Files:**
- Rewrite: `frontend/src/pages/student/DiscoverHomePage.tsx`
- Create: `frontend/src/pages/student/discover/UniConversation.tsx`
- Modify: `frontend/src/api/discovery.ts` (`startUnifiedSession`)
- Test: `frontend/src/pages/student/discover/__tests__/UniConversation.test.tsx`

- [ ] **Step 1: Failing test** — Discover renders a single column with Uni's opener and no track/rail chrome:

```tsx
test('Discover shows Uni conversation, no track tabs or rails', async () => {
  renderWithProviders(<DiscoverHomePage />)
  expect(await screen.findByText(/I'm Uni/i)).toBeInTheDocument()
  expect(screen.queryByText(/Profile/)).not.toBeInTheDocument()      // no track tab
  expect(screen.queryByText(/Readiness/)).not.toBeInTheDocument()    // no rail
})
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** `UniConversation.tsx` (bubbles with "U" avatar, warm opener from spec §3.3, one-at-a-time turns, counselor quick-replies "I'm not sure where to start"/"Could you give an example?"/"You ask me", composer, streaming dots) and rewrite `DiscoverHomePage.tsx` to render only the Uni header + `<UniConversation/>` + the "✦ Your profile ▸" trigger. Remove `TrackSelector`, `LayerSwitcher`, `StrategyHandoffCTA`, `ReadinessRail`, `ArtifactRail` imports/usage. Use `startUnifiedSession`.

- [ ] **Step 4: Run test + `npx tsc --noEmit` → PASS.**

- [ ] **Step 5: Commit** `feat(discover): single-column Uni conversation, remove track/rail UI`.

### Task 6: Inline editable "Noticed" cards

**Files:** Create `frontend/src/pages/student/discover/NoticedCard.tsx`; modify `UniConversation.tsx`; modify `api/discovery.ts` (`updateSignal`); test `__tests__/NoticedCard.test.tsx`.

- [ ] **Step 1: Failing test** — a turn with an extracted signal renders a "✓ Noticed…" card with a working ✎ edit that calls `updateSignal`.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** `NoticedCard` (reads `extracted_signals` from the assistant turn; shows "✓ Noticed: <summary>" + ✎; edit opens an inline input → `updateSignal(signalId, value)` → optimistic update). Render it inline in the thread when a turn carries a new signal.
- [ ] **Step 4: Run + tsc → PASS.**
- [ ] **Step 5: Commit** `feat(discover): inline editable Noticed confirmation cards`.

### Task 7: Living-profile slide-over drawer

**Files:** Create `frontend/src/pages/student/discover/ProfileDrawer.tsx`; modify `api/discovery.ts` (`getLivingProfile`); modify `DiscoverHomePage.tsx`; test `__tests__/ProfileDrawer.test.tsx`.

- [ ] **Step 1: Failing test** — clicking "✦ Your profile ▸" opens a drawer with the narrative + "What lights you up / Where you're headed / What you need to thrive" sections + a gap invitation; editing a chip calls `updateSignal`.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** `ProfileDrawer` (slide-over; reads `getLivingProfile` = synthesized narrative + grouped editable chips from goals/needs/identity; gaps as "Uni could understand you better if we talk about … →" that dispatches a conversation prompt; dismissible). Wire the trigger in `DiscoverHomePage`.
- [ ] **Step 4: Run + tsc → PASS.**
- [ ] **Step 5: Commit** `feat(discover): living-profile slide-over drawer`.

### Task 8: In-thread counselor-led match handoff

**Files:** Create `frontend/src/pages/student/discover/MatchHandoffCard.tsx`; modify `UniConversation.tsx`; test `__tests__/MatchHandoffCard.test.tsx`.

- [ ] **Step 1: Failing test** — when the latest turn's readiness signal says ready, an in-thread card renders Uni's offer + "See programs that fit me →" navigating to `/s/explore` (and "Keep talking" dismisses); the card also renders on demand with a confidence note.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** `MatchHandoffCard` (reads the existing handoff verdict; warm message from spec §3.5; primary → existing strategy/match flow → `/s/explore`; secondary "Keep talking"; always-available variant shows the honest confidence note).
- [ ] **Step 4: Run + tsc → PASS.**
- [ ] **Step 5: Commit** `feat(discover): in-thread counselor-led match handoff`.

---

## Phase C — Verify & ship

### Task 9: Regression, flags, fallback, full suites

- [ ] **Step 1:** Backend — run `tests/test_match_*.py`, `tests/test_plan2_integration.py`, the new `test_unified_discovery_extraction.py`, `test_uni_*` on an isolated DB; confirm matching/strategy/profile read the same signals and the rule-based fallback path still returns 200 with the flag off. Capture `; echo EXIT=$?`.
- [ ] **Step 2:** Frontend — `npx vitest run` + `npx tsc --noEmit` green.
- [ ] **Step 3:** `ruff check src tests` + frontend eslint clean.
- [ ] **Step 4: Commit** any fixes; open the PR.

---

## Self-Review

**Spec coverage:** §3.1 persona/voice → Task 1; §3.2 playbook → Tasks 1+4; §3.3 conversation UX → Tasks 5+6; §3.4 living profile → Task 7; §3.5 handoff → Task 8; §4.1 frontend keep/replace/remove/add → Tasks 5–8; §4.2 backend keep/change → Tasks 1–3; §4.3 data flow → Tasks 3+7+8; §5 fallback → Tasks 3+9; §6 testing → every task + Task 9; §7 non-goals respected (no matching/strategy/table changes beyond an additive CHECK widen). No gaps.

**Placeholder scan:** code shown for every novel/critical step; large UI components specify exact files, props, behaviors, and tests (full line-by-line markup is the implementation, produced per-task under TDD). Pseudocode blocks are explicitly marked and bounded.

**Type consistency:** `startUnifiedSession` / `updateSignal` / `getLivingProfile` (api/discovery.ts) and `track="discovery"` are used consistently across backend Tasks 2–3 and frontend Tasks 5–8.

## Notes for the executor
- Work on `claude/discover-uni-redesign-8bf9e6`. Coordinate (`git fetch origin main` + merge) before pushing; Discover/types/test-list are hot files.
- Feature-flag the new Discover behind the existing discovery flag so it can ship dark, then flip per the standing prod-flag practice.
- Per the project owner: after this plan is approved, implementation + online deploy proceed autonomously (no further per-step approval).
