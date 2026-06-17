# My Space Home Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the `/s/space` home as a focus → momentum → density synthesis: a Today's-focus hero, a momentum band (onboarding ring + journey-stage map + this-week ribbon), the existing dense dashboard with count-up stats and an earned-gold Offers tile, a strategy snapshot, and smart empty states everywhere.

**Architecture:** Frontend-only, zero backend changes — pure client-side composition of endpoints the home already calls (one new query, `getActiveStrategy`). The ~370-line `MySpaceHomePage.tsx` is decomposed into small, independently-tested `home/*` modules: pure helpers (`upNext`, `weekActivity`, `journeyStage`, `celebrate`) and presentational components (`TodaysFocus`, `MomentumBand`, `JourneyMap`, `WeekRibbon`, `ProgressRing`, `StrategySnapshot`). `JourneyChecklistCard.tsx` is deleted, its body absorbed into `MomentumBand`.

**Tech Stack:** React 19 + TS + TanStack Query + Tailwind; vitest + @testing-library/react. Spec: `docs/superpowers/specs/2026-06-14-myspace-home-redesign-design.md`.

**Conventions (apply to every task):**
- Code style: single quotes, no semicolons (match surrounding files). 2-space indent.
- Typecheck: `cd frontend && npx tsc -p tsconfig.app.json --noEmit` (the root `tsconfig.json` is references-only — plain `tsc --noEmit` checks nothing).
- Single test file: `cd frontend && npx vitest run src/test/<file>`.
- Branch is `claude/myspace-redesign` (already created off main). Work here; do NOT create another branch/worktree.
- Before each commit, purge iCloud dup files: `git ls-files | grep ' 2\.'` must be empty; `find frontend/src -name '* 2.*' -delete` if any appear. Stage only the files the task names — never `git add -A`.
- Every commit message ends with the trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

**Brand constraints (enforced throughout):** full-bleed `w-full` (no `max-w`); gold (`--primary`/`text-primary`) ONLY on the onboarding ring, the Offers tile when offers exist, and the one-shot win beat; cobalt (`--secondary`/`text-secondary`) for journey map + all chrome; all JS motion gates via `prefersReducedMotion()`.

---

### Task 1: Extract the Up-next priority builder (`home/upNext.ts`)

Pull the inline `upNext` computation and `NextAction` type out of `MySpaceHomePage.tsx` into a pure, tested module. `TodaysFocus` will render `[0]`; the Up-next section renders `.slice(1)`.

**Files:**
- Create: `frontend/src/pages/student/myspace/home/upNext.ts`
- Create: `frontend/src/test/myspace-upnext.test.ts`
- Modify: `frontend/src/pages/student/myspace/MySpaceHomePage.tsx`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/test/myspace-upnext.test.ts
import { describe, expect, it } from 'vitest'
import { buildUpNext, type UpNextInputs } from '../pages/student/myspace/home/upNext'

const base: UpNextInputs = {
  calItems: [],
  offers: [],
  drafts: [],
  pendingClarifications: 0,
}

describe('buildUpNext', () => {
  it('orders overdue → offer → interview → draft → clarification and caps at 5', () => {
    const inputs: UpNextInputs = {
      calItems: [
        { id: 'o1', title: 'Late thing', status: 'overdue', subtitle: null, institution_name: 'X', can_confirm: false, start_at: '2026-01-01' },
        { id: 'iv', title: 'Interview', status: 'scheduled', subtitle: null, institution_name: 'Y', can_confirm: true, start_at: '2026-07-01' },
      ] as any,
      offers: [{ id: 'a1', status: 'decision_made', decision: 'admitted', student_decision: null, program: { program_name: 'CS', institution_name: 'MIT' } }] as any,
      drafts: [{ id: 'd1', status: 'draft', readiness_pct: 80, program: { program_name: 'EE' } }] as any,
      pendingClarifications: 2,
    }
    const out = buildUpNext(inputs)
    expect(out.map(a => a.chip)).toEqual(['overdue', 'offer in', 'slots held', 'draft', 'quick win'])
    expect(out.length).toBeLessThanOrEqual(5)
  })

  it('returns [] when nothing is pending', () => {
    expect(buildUpNext(base)).toEqual([])
  })

  it('drops offers the student already decided on', () => {
    const out = buildUpNext({ ...base, offers: [{ id: 'a', status: 'decision_made', decision: 'admitted', student_decision: 'accepted_by_student', program: {} }] as any })
    expect(out).toEqual([])
  })
})
```

- [ ] **Step 2: Run it — `npx vitest run src/test/myspace-upnext.test.ts` — Expected: FAIL (module not found).**

- [ ] **Step 3: Create `home/upNext.ts`** by lifting the exact logic from `MySpaceHomePage.tsx` (the current inline `upNext` IIFE, the `NextAction` type, `daysUntil` is NOT needed here, and the `programLabel` helper):

```ts
import { AlertTriangle, Award, Calendar as CalendarIcon, Compass, PenLine } from 'lucide-react'
import type { Application } from '../../../../types'
import type { CalendarItem } from '../../../../api/calendar'

export type NextAction = {
  key: string
  icon: typeof PenLine
  title: string
  sub: string
  urgency: 'danger' | 'warning' | 'neutral'
  chip: string
  to: string
}

export interface UpNextInputs {
  calItems: CalendarItem[]
  offers: Application[]
  drafts: Application[]
  pendingClarifications: number
}

function programLabel(app: Application): string {
  return app.program?.program_name ?? 'your program'
}

/** Priority order across the cycle, capped at 5 (Spec 2026-06-10 §4). */
export function buildUpNext({ calItems, offers, drafts, pendingClarifications }: UpNextInputs): NextAction[] {
  const actions: NextAction[] = []
  for (const item of calItems.filter(i => i.status === 'overdue').slice(0, 2)) {
    actions.push({
      key: `overdue-${item.id}`,
      icon: AlertTriangle,
      title: item.title,
      sub: item.subtitle ?? item.institution_name ?? 'Overdue',
      urgency: 'danger',
      chip: 'overdue',
      to: '/s/calendar',
    })
  }
  for (const app of offers.filter(a => !a.student_decision)) {
    actions.push({
      key: `offer-${app.id}`,
      icon: Award,
      title: `Respond to your offer — ${programLabel(app)}`,
      sub: app.program?.institution_name ?? 'Decision needed',
      urgency: 'warning',
      chip: 'offer in',
      to: `/s/applications/${app.id}?tab=offer`,
    })
  }
  for (const item of calItems.filter(i => i.can_confirm)) {
    actions.push({
      key: `interview-${item.id}`,
      icon: CalendarIcon,
      title: item.title,
      sub: 'Pick a time that works for you',
      urgency: 'warning',
      chip: 'slots held',
      to: '/s/prep?tab=interviews',
    })
  }
  for (const app of drafts.slice().sort((a, b) => (b.readiness_pct ?? 0) - (a.readiness_pct ?? 0))) {
    actions.push({
      key: `draft-${app.id}`,
      icon: PenLine,
      title: `Continue ${programLabel(app)}`,
      sub: app.readiness_pct != null ? `${Math.round(app.readiness_pct)}% ready to submit` : 'In progress',
      urgency: 'neutral',
      chip: 'draft',
      to: `/s/applications/${app.id}`,
    })
  }
  if (pendingClarifications > 0) {
    actions.push({
      key: 'clarifications',
      icon: Compass,
      title: `Answer ${pendingClarifications} quick question${pendingClarifications === 1 ? '' : 's'} from Uni`,
      sub: 'Sharpens your matches and readiness',
      urgency: 'neutral',
      chip: 'quick win',
      to: '/s',
    })
  }
  return actions.slice(0, 5)
}
```

- [ ] **Step 4: Run it — Expected: PASS (3 tests).**

- [ ] **Step 5: Refactor `MySpaceHomePage.tsx` to consume it (no behavior change yet).** Remove the inline `NextAction` type and the `upNext` IIFE; import and call `buildUpNext`:

```ts
// add import at top:
import { buildUpNext, type NextAction } from './home/upNext'
```
Replace the inline `const upNext: NextAction[] = (() => { ... })()` block with:
```ts
const upNext = buildUpNext({ calItems, offers, drafts, pendingClarifications })
```
Keep `daysUntil` and `programLabel` only if still referenced elsewhere in the file (`daysUntil` is — keep it; `programLabel` is now unused in the page → delete it from the page).

- [ ] **Step 6: Verify — `npx tsc -p tsconfig.app.json --noEmit` (0 errors) and `npx vitest run src/test/myspace-upnext.test.ts` (PASS).**

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/student/myspace/home/upNext.ts frontend/src/test/myspace-upnext.test.ts frontend/src/pages/student/myspace/MySpaceHomePage.tsx
git commit -m "refactor(myspace): extract buildUpNext priority builder"
```

---

### Task 2: This-week activity counter (`home/weekActivity.ts`)

**Files:**
- Create: `frontend/src/pages/student/myspace/home/weekActivity.ts`
- Create: `frontend/src/test/myspace-week.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/test/myspace-week.test.ts
import { describe, expect, it } from 'vitest'
import { countThisWeek, type WeekInputs } from '../pages/student/myspace/home/weekActivity'

const iso = (daysAgo: number) => new Date(Date.now() - daysAgo * 86_400_000).toISOString()

describe('countThisWeek', () => {
  it('counts only items within the last 7 days', () => {
    const inputs: WeekInputs = {
      saved: [{ added_at: iso(2) }, { added_at: iso(10) }] as any,
      runs: [{ created_at: iso(1) }] as any,
      apps: [{ submitted_at: iso(3) }, { submitted_at: null }, { submitted_at: iso(30) }] as any,
    }
    expect(countThisWeek(inputs)).toEqual({ saved: 1, reviewed: 1, submitted: 1, total: 3 })
  })

  it('is all-zero for an empty week', () => {
    expect(countThisWeek({ saved: [], runs: [], apps: [] })).toEqual({ saved: 0, reviewed: 0, submitted: 0, total: 0 })
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL (module not found).**

- [ ] **Step 3: Implement**

```ts
// frontend/src/pages/student/myspace/home/weekActivity.ts
import type { Application, SavedProgram, WorkshopFeedbackRun } from '../../../../types'

export interface WeekInputs {
  saved: Pick<SavedProgram, 'added_at'>[]
  runs: Pick<WorkshopFeedbackRun, 'created_at'>[]
  apps: Pick<Application, 'submitted_at'>[]
}

export interface WeekCounts {
  saved: number
  reviewed: number
  submitted: number
  total: number
}

const WEEK_MS = 7 * 86_400_000

function within7d(iso: string | null | undefined): boolean {
  if (!iso) return false
  const t = new Date(iso).getTime()
  return Number.isFinite(t) && Date.now() - t <= WEEK_MS && Date.now() - t >= 0
}

/** Count last-7-day activity from the three timestamped sources the home
 *  already fetches (Spec 2026-06-14 §Modules.2c). */
export function countThisWeek({ saved, runs, apps }: WeekInputs): WeekCounts {
  const s = saved.filter(x => within7d(x.added_at)).length
  const r = runs.filter(x => within7d(x.created_at)).length
  const sub = apps.filter(x => within7d(x.submitted_at)).length
  return { saved: s, reviewed: r, submitted: sub, total: s + r + sub }
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/student/myspace/home/weekActivity.ts frontend/src/test/myspace-week.test.ts
git commit -m "feat(myspace): this-week activity counter"
```

---

### Task 3: Journey-stage derivation (`home/journeyStage.ts`)

**Files:**
- Create: `frontend/src/pages/student/myspace/home/journeyStage.ts`
- Create: `frontend/src/test/myspace-stage.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/test/myspace-stage.test.ts
import { describe, expect, it } from 'vitest'
import { deriveStage, STAGES, type StageInputs } from '../pages/student/myspace/home/journeyStage'

const base: StageInputs = { savedCount: 0, appCount: 0, hasDecision: false, hasOffer: false }

describe('deriveStage', () => {
  it('defaults to Discover with no signals', () => {
    expect(deriveStage(base)).toBe('discover')
  })
  it('reaches Match when programs are saved', () => {
    expect(deriveStage({ ...base, savedCount: 3 })).toBe('match')
  })
  it('reaches Apply when an application exists', () => {
    expect(deriveStage({ ...base, savedCount: 3, appCount: 1 })).toBe('apply')
  })
  it('reaches Decide on a decision or offer', () => {
    expect(deriveStage({ ...base, appCount: 2, hasOffer: true })).toBe('decide')
    expect(deriveStage({ ...base, appCount: 2, hasDecision: true })).toBe('decide')
  })
  it('exposes the four ordered stages', () => {
    expect(STAGES.map(s => s.key)).toEqual(['discover', 'match', 'apply', 'decide'])
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL.**

- [ ] **Step 3: Implement**

```ts
// frontend/src/pages/student/myspace/home/journeyStage.ts
export type StageKey = 'discover' | 'match' | 'apply' | 'decide'

export const STAGES: { key: StageKey; label: string; to: string }[] = [
  { key: 'discover', label: 'Discover', to: '/s' },
  { key: 'match', label: 'Match', to: '/s/explore' },
  { key: 'apply', label: 'Apply', to: '/s/applications' },
  { key: 'decide', label: 'Decide', to: '/s/applications?tab=offers' },
]

export interface StageInputs {
  savedCount: number
  appCount: number
  hasDecision: boolean
  hasOffer: boolean
}

/** Furthest-reached stage from data the home already fetches (Spec 2026-06-14
 *  §Modules.2b). Match is inferred from saved programs (the home fetches saved
 *  but not matches), so no extra query is added. */
export function deriveStage({ savedCount, appCount, hasDecision, hasOffer }: StageInputs): StageKey {
  if (hasDecision || hasOffer) return 'decide'
  if (appCount > 0) return 'apply'
  if (savedCount > 0) return 'match'
  return 'discover'
}

export function stageIndex(key: StageKey): number {
  return STAGES.findIndex(s => s.key === key)
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/student/myspace/home/journeyStage.ts frontend/src/test/myspace-stage.test.ts
git commit -m "feat(myspace): journey-stage derivation"
```

---

### Task 4: Win-celebration tracker (`home/celebrate.ts`)

A win beats its gold pulse exactly once, ever — tracked by id in localStorage.

**Files:**
- Create: `frontend/src/pages/student/myspace/home/celebrate.ts`
- Create: `frontend/src/test/myspace-celebrate.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/test/myspace-celebrate.test.ts
import { beforeEach, describe, expect, it } from 'vitest'
import { freshWinIds, markCelebrated, CELEBRATE_KEY } from '../pages/student/myspace/home/celebrate'

describe('celebrate', () => {
  beforeEach(() => localStorage.clear())

  it('returns all ids on first sight, none after marking', () => {
    expect(freshWinIds(['offer-a', 'offer-b'])).toEqual(['offer-a', 'offer-b'])
    markCelebrated(['offer-a', 'offer-b'])
    expect(freshWinIds(['offer-a', 'offer-b'])).toEqual([])
  })

  it('only the new id is fresh after a prior celebration', () => {
    markCelebrated(['offer-a'])
    expect(freshWinIds(['offer-a', 'offer-b'])).toEqual(['offer-b'])
  })

  it('survives malformed storage', () => {
    localStorage.setItem(CELEBRATE_KEY, 'not json')
    expect(freshWinIds(['x'])).toEqual(['x'])
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL.**

- [ ] **Step 3: Implement**

```ts
// frontend/src/pages/student/myspace/home/celebrate.ts
export const CELEBRATE_KEY = 'myspace_celebrated'

function read(): Set<string> {
  try {
    const raw = localStorage.getItem(CELEBRATE_KEY)
    if (!raw) return new Set()
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? new Set(arr.map(String)) : new Set()
  } catch {
    return new Set()
  }
}

/** Win ids not yet celebrated. */
export function freshWinIds(ids: string[]): string[] {
  const seen = read()
  return ids.filter(id => !seen.has(id))
}

/** Persist that these win ids have had their one gold beat. */
export function markCelebrated(ids: string[]): void {
  if (!ids.length) return
  try {
    const seen = read()
    ids.forEach(id => seen.add(id))
    localStorage.setItem(CELEBRATE_KEY, JSON.stringify([...seen]))
  } catch {
    /* ignore — celebration is best-effort */
  }
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/student/myspace/home/celebrate.ts frontend/src/test/myspace-celebrate.test.ts
git commit -m "feat(myspace): one-shot win-celebration tracker"
```

---

### Task 5: Extract `ProgressRing` into its own file

`ProgressRing` currently lives inside `JourneyChecklistCard.tsx` (lines ~47–88). Move it verbatim into `home/ProgressRing.tsx` so `MomentumBand` can reuse it; update `JourneyChecklistCard` to import it (interim — the card is deleted in Task 8).

**Files:**
- Create: `frontend/src/pages/student/myspace/home/ProgressRing.tsx`
- Modify: `frontend/src/pages/student/myspace/JourneyChecklistCard.tsx`

- [ ] **Step 1: Create `home/ProgressRing.tsx`** with the exact component (copy the `ProgressRing` function + its doc comment from `JourneyChecklistCard.tsx`):

```tsx
// Gold progress ring — mounts empty, then a double rAF flips `drawn` so the
// 0.8s dashoffset transition plays the initial fill (DualRing's pattern).
// Reduced motion mounts pre-drawn; the numeral counts up alongside.
// (UX overhaul Ship C §3; extracted for reuse by the My Space momentum band.)
import { useEffect, useState } from 'react'
import { prefersReducedMotion, useCountUp } from '../../../../hooks/useCountUp'

export default function ProgressRing({ pct, size = 64, stroke = 6 }: { pct: number; size?: number; stroke?: number }) {
  const [drawn, setDrawn] = useState(() => prefersReducedMotion())
  useEffect(() => {
    if (drawn) return
    let raf2 = 0
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => setDrawn(true))
    })
    return () => {
      cancelAnimationFrame(raf1)
      cancelAnimationFrame(raf2)
    }
  }, [drawn])

  const counted = useCountUp(pct)
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const offset = drawn ? c * (1 - pct / 100) : c

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }} aria-hidden>
      <svg width={size} height={size} className="-rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(var(--border))" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center leading-none">
        <span className="text-base font-bold text-foreground tabular-nums">{counted}%</span>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Update `JourneyChecklistCard.tsx`** — delete its inline `ProgressRing` function (and the now-unused `prefersReducedMotion`/`useCountUp` imports if they were only used by it; `useCountUp` is only used by `ProgressRing`, so remove both from this file's imports), add `import ProgressRing from './home/ProgressRing'`. The `<ProgressRing pct={data.completion_percentage} />` usage stays.

- [ ] **Step 3: Verify — `npx tsc -p tsconfig.app.json --noEmit` (0 errors).** No new test (pure move; covered by the existing app + Task 8 smoke).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/student/myspace/home/ProgressRing.tsx frontend/src/pages/student/myspace/JourneyChecklistCard.tsx
git commit -m "refactor(myspace): extract ProgressRing for reuse"
```

---

### Task 6: Journey-map component (`home/JourneyMap.tsx`)

**Files:**
- Create: `frontend/src/pages/student/myspace/home/JourneyMap.tsx`
- Create: `frontend/src/test/myspace-journeymap.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/test/myspace-journeymap.test.tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import JourneyMap from '../pages/student/myspace/home/JourneyMap'

const renderMap = (props: React.ComponentProps<typeof JourneyMap>) =>
  render(<MemoryRouter><JourneyMap {...props} /></MemoryRouter>)

describe('JourneyMap', () => {
  it('marks the derived current stage with aria-current', () => {
    renderMap({ savedCount: 2, appCount: 0, hasDecision: false, hasOffer: false })
    expect(screen.getByText('Match').closest('[aria-current="step"]')).not.toBeNull()
  })
  it('renders all four stage labels', () => {
    renderMap({ savedCount: 0, appCount: 0, hasDecision: false, hasOffer: false })
    for (const label of ['Discover', 'Match', 'Apply', 'Decide']) {
      expect(screen.getByText(label)).toBeTruthy()
    }
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL.**

- [ ] **Step 3: Implement** (cobalt for reached/current, muted for future; nodes deep-link):

```tsx
// frontend/src/pages/student/myspace/home/JourneyMap.tsx
import { useNavigate } from 'react-router-dom'
import { Check } from 'lucide-react'
import { STAGES, deriveStage, stageIndex, type StageInputs } from './journeyStage'

/** Horizontal Discover › Match › Apply › Decide track. The current stage is
 *  lit in cobalt; reached stages are filled; future stages muted. Chrome →
 *  cobalt, never gold (Spec 2026-06-14 §Modules.2b). */
export default function JourneyMap(props: StageInputs) {
  const navigate = useNavigate()
  const current = deriveStage(props)
  const curIdx = stageIndex(current)

  return (
    <div className="flex items-center gap-1" role="list" aria-label="Your journey">
      {STAGES.map((s, i) => {
        const reached = i <= curIdx
        const isCurrent = i === curIdx
        return (
          <div key={s.key} className="flex flex-1 items-center" role="listitem">
            <button
              onClick={() => navigate(s.to)}
              aria-current={isCurrent ? 'step' : undefined}
              className="group flex flex-col items-center gap-1 min-w-0 flex-shrink-0"
            >
              <span
                className={`flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold transition-colors ${
                  isCurrent
                    ? 'bg-secondary text-secondary-foreground ring-2 ring-secondary/30'
                    : reached
                      ? 'bg-secondary/15 text-secondary'
                      : 'bg-muted text-muted-foreground'
                }`}
              >
                {reached && !isCurrent ? <Check size={12} /> : i + 1}
              </span>
              <span className={`text-[10px] font-medium ${isCurrent ? 'text-secondary' : reached ? 'text-foreground' : 'text-muted-foreground'}`}>
                {s.label}
              </span>
            </button>
            {i < STAGES.length - 1 && (
              <span className={`mx-1 h-0.5 flex-1 rounded-full ${i < curIdx ? 'bg-secondary/40' : 'bg-border'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/student/myspace/home/JourneyMap.tsx frontend/src/test/myspace-journeymap.test.tsx
git commit -m "feat(myspace): journey-stage map"
```

---

### Task 7: Week-ribbon component (`home/WeekRibbon.tsx`)

**Files:**
- Create: `frontend/src/pages/student/myspace/home/WeekRibbon.tsx`
- Create: `frontend/src/test/myspace-weekribbon.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/test/myspace-weekribbon.test.tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import WeekRibbon from '../pages/student/myspace/home/WeekRibbon'

const iso = (d: number) => new Date(Date.now() - d * 86_400_000).toISOString()

describe('WeekRibbon', () => {
  it('shows only non-zero segments', () => {
    render(<WeekRibbon saved={[{ added_at: iso(1) }] as any} runs={[]} apps={[{ submitted_at: iso(2) }] as any} />)
    expect(screen.getByText(/1 saved/)).toBeTruthy()
    expect(screen.getByText(/1 submitted/)).toBeTruthy()
    expect(screen.queryByText(/reviewed/)).toBeNull()
  })
  it('shows the smart-empty prompt on a quiet week', () => {
    render(<WeekRibbon saved={[]} runs={[]} apps={[]} />)
    expect(screen.getByText(/quiet week/i)).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL.**

- [ ] **Step 3: Implement**

```tsx
// frontend/src/pages/student/myspace/home/WeekRibbon.tsx
import { Sparkles } from 'lucide-react'
import { countThisWeek, type WeekInputs } from './weekActivity'

/** "This week · +N saved · N reviewed · N submitted" — only non-zero segments;
 *  a smart-empty prompt on a quiet week (Spec 2026-06-14 §Modules.2c). */
export default function WeekRibbon(inputs: WeekInputs) {
  const c = countThisWeek(inputs)
  const segments: string[] = []
  if (c.saved) segments.push(`${c.saved} saved`)
  if (c.reviewed) segments.push(`${c.reviewed} reviewed`)
  if (c.submitted) segments.push(`${c.submitted} submitted`)

  return (
    <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2">
      <Sparkles size={13} className="shrink-0 text-secondary" aria-hidden />
      {c.total === 0 ? (
        <p className="text-xs text-muted-foreground">A quiet week so far — pick one thing below to move forward.</p>
      ) : (
        <p className="text-xs text-foreground">
          <span className="font-semibold">This week</span>
          <span className="text-muted-foreground"> · {segments.join(' · ')}</span>
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/student/myspace/home/WeekRibbon.tsx frontend/src/test/myspace-weekribbon.test.tsx
git commit -m "feat(myspace): this-week momentum ribbon"
```

---

### Task 8: Momentum band (`home/MomentumBand.tsx`) — absorbs JourneyChecklistCard

Compose the onboarding ring + next-3 setup steps (absorbing `JourneyChecklistCard`'s body) with `JourneyMap` and `WeekRibbon`. The band always renders; the ring + steps self-hide at 100%. Then delete `JourneyChecklistCard.tsx`.

**Files:**
- Create: `frontend/src/pages/student/myspace/home/MomentumBand.tsx`
- Create: `frontend/src/test/myspace-momentum.test.tsx`
- Delete: `frontend/src/pages/student/myspace/JourneyChecklistCard.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/test/myspace-momentum.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/students', () => ({ getOnboarding: vi.fn() }))
import { getOnboarding } from '../api/students'
import MomentumBand from '../pages/student/myspace/home/MomentumBand'

const onboarding = vi.mocked(getOnboarding)

function renderBand(props: React.ComponentProps<typeof MomentumBand>) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}><MemoryRouter><MomentumBand {...props} /></MemoryRouter></QueryClientProvider>,
  )
}

const stage = { savedCount: 1, appCount: 0, hasDecision: false, hasOffer: false }
const week = { saved: [], runs: [], apps: [] }

describe('MomentumBand', () => {
  it('shows the setup ring + a next step while onboarding < 100%', async () => {
    onboarding.mockResolvedValue({ completion_percentage: 40, steps_completed: ['basic_profile'], next_step: null } as any)
    renderBand({ stage, week })
    expect(await screen.findByText('Set up your space')).toBeTruthy()
    expect(screen.getByText('Match')).toBeTruthy() // journey map still renders
  })
  it('hides the ring at 100% but still renders the journey map', async () => {
    onboarding.mockResolvedValue({ completion_percentage: 100, steps_completed: [], next_step: null } as any)
    renderBand({ stage, week })
    await waitFor(() => expect(screen.getByText('Match')).toBeTruthy())
    expect(screen.queryByText('Set up your space')).toBeNull()
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL (module not found).**

- [ ] **Step 3: Implement** (move `STEP_SPECS` + the `getOnboarding` query + the next-3-steps list out of `JourneyChecklistCard` into the band, alongside `JourneyMap` + `WeekRibbon`):

```tsx
// frontend/src/pages/student/myspace/home/MomentumBand.tsx
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, CheckCircle2, ListChecks } from 'lucide-react'

import Card from '../../../../components/ui/Card'
import { ListRow } from '../../../../components/student/density'
import { getOnboarding } from '../../../../api/students'
import { track } from '../../../../lib/analytics'
import type { OnboardingStatus } from '../../../../types'
import ProgressRing from './ProgressRing'
import JourneyMap from './JourneyMap'
import WeekRibbon from './WeekRibbon'
import type { StageInputs } from './journeyStage'
import type { WeekInputs } from './weekActivity'

// The onboarding engine's step keys mapped to the route that completes each
// (moved verbatim from the retired JourneyChecklistCard).
const STEP_SPECS: { key: string; label: string; sub: string; to: string }[] = [
  { key: 'basic_profile', label: 'Add your basic info', sub: 'Name and nationality unlock everything else', to: '/s/profile' },
  { key: 'academics', label: 'Add an academic record', sub: 'Match scores improve once we know your grades', to: '/s/profile?tab=academics' },
  { key: 'test_scores', label: 'Add a test score', sub: 'SAT, GRE, IELTS — whatever you have', to: '/s/profile?tab=academics' },
  { key: 'activities', label: 'Add an activity', sub: 'Clubs, projects, anything you give time to', to: '/s/profile?tab=experience' },
  { key: 'online_presence', label: 'Link your LinkedIn or portfolio', sub: 'Links strengthen your other entries', to: '/s/profile?tab=experience' },
  { key: 'portfolio', label: 'Showcase a project', sub: 'A work sample makes your story concrete', to: '/s/profile?tab=experience' },
  { key: 'research', label: 'Add research experience', sub: 'Labs, papers, independent projects', to: '/s/profile?tab=academics' },
  { key: 'languages', label: 'Add the languages you speak', sub: 'Programs care about language fit', to: '/s/profile?tab=academics' },
  { key: 'work_experience', label: 'Add work or volunteer experience', sub: 'Internships and jobs count', to: '/s/profile?tab=experience' },
  { key: 'competitions', label: 'Add a competition', sub: 'Olympiads, hackathons, case comps', to: '/s/profile?tab=experience' },
  { key: 'goals', label: 'Describe your goals', sub: 'Sharpens your strategy and rationales', to: '/s/profile?tab=goals' },
  { key: 'preferences', label: 'Set program preferences', sub: 'Location, budget and format filter your matches', to: '/s/profile?tab=preferences' },
]

interface Props {
  stage: StageInputs
  week: WeekInputs
  className?: string
}

export default function MomentumBand({ stage, week, className }: Props) {
  const navigate = useNavigate()
  const { data } = useQuery<OnboardingStatus>({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
    staleTime: 60_000,
  })

  const pct = data?.completion_percentage ?? 100
  const showSetup = !!data && pct < 100
  const done = new Set(data?.steps_completed ?? [])
  const nextSteps = STEP_SPECS.filter(s => !done.has(s.key)).slice(0, 3)

  const goTo = (step: { key: string; to: string }) => {
    track('onboarding_checklist_step_clicked', { step: step.key, to: step.to })
    navigate(step.to)
  }

  return (
    <Card pad={false} className={`p-5 ${className ?? ''}`}>
      {/* Journey-stage map — always present. */}
      <JourneyMap {...stage} />

      {/* This-week ribbon — always present. */}
      <div className="mt-4">
        <WeekRibbon {...week} />
      </div>

      {/* Setup ring + next steps — only while onboarding is incomplete. */}
      {showSetup && nextSteps.length > 0 && (
        <div className="mt-4 border-t border-border pt-4">
          <div className="flex items-center gap-4">
            <ProgressRing pct={pct} />
            <div className="min-w-0 flex-1">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <ListChecks size={15} className="text-secondary" aria-hidden /> Set up your space
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">Each step sharpens your matches — pick up wherever you like.</p>
            </div>
            {done.size > 0 && (
              <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[11px] font-semibold text-muted-foreground">
                <CheckCircle2 size={12} className="text-success" aria-hidden /> {done.size} done
              </span>
            )}
          </div>
          <div className="stagger-list mt-3">
            {nextSteps.map(step => (
              <ListRow
                key={step.key}
                title={step.label}
                sub={step.sub}
                trailing={<ArrowRight size={14} className="text-secondary" aria-hidden />}
                onClick={() => goTo(step)}
              />
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Delete `JourneyChecklistCard.tsx`** (`git rm frontend/src/pages/student/myspace/JourneyChecklistCard.tsx`). Its only importer is `MySpaceHomePage.tsx`, rewired in Task 11.

- [ ] **Step 6: Verify — `npx tsc -p tsconfig.app.json --noEmit`.** Expect ONE error: `MySpaceHomePage.tsx` still imports the deleted card. That's fixed in Task 11; to keep this commit green, in `MySpaceHomePage.tsx` remove the `import JourneyChecklistCard` line and its two `<JourneyChecklistCard … />` usages now (leaving a temporary gap the Task 11 rewrite fills). Re-run tsc → 0 errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/student/myspace/home/MomentumBand.tsx frontend/src/test/myspace-momentum.test.tsx frontend/src/pages/student/myspace/MySpaceHomePage.tsx
git rm frontend/src/pages/student/myspace/JourneyChecklistCard.tsx
git commit -m "feat(myspace): momentum band (ring + journey map + week ribbon), retire JourneyChecklistCard"
```

---

### Task 9: Today's-focus hero (`home/TodaysFocus.tsx`)

**Files:**
- Create: `frontend/src/pages/student/myspace/home/TodaysFocus.tsx`
- Create: `frontend/src/test/myspace-focus.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/test/myspace-focus.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import TodaysFocus from '../pages/student/myspace/home/TodaysFocus'
import { AlertTriangle } from 'lucide-react'

const nav = vi.fn()
vi.mock('react-router-dom', async (orig) => ({ ...(await orig() as object), useNavigate: () => nav }))

describe('TodaysFocus', () => {
  it('renders the top action and navigates on click', () => {
    render(
      <MemoryRouter>
        <TodaysFocus action={{ key: 'k', icon: AlertTriangle, title: 'Respond to your offer', sub: 'MIT', urgency: 'warning', chip: 'offer in', to: '/s/applications/1?tab=offer' }} onboardingComplete={false} />
      </MemoryRouter>,
    )
    expect(screen.getByText('Respond to your offer')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /respond to your offer/i }))
    expect(nav).toHaveBeenCalledWith('/s/applications/1?tab=offer')
  })

  it('shows the caught-up state with a setup CTA when no action and onboarding incomplete', () => {
    render(<MemoryRouter><TodaysFocus action={null} onboardingComplete={false} /></MemoryRouter>)
    expect(screen.getByText(/caught up/i)).toBeTruthy()
    expect(screen.getByText(/Keep building your profile/i)).toBeTruthy()
  })

  it('caught-up CTA points to Uni when onboarding is complete', () => {
    render(<MemoryRouter><TodaysFocus action={null} onboardingComplete /></MemoryRouter>)
    expect(screen.getByText(/Talk to Uni/i)).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL.**

- [ ] **Step 3: Implement**

```tsx
// frontend/src/pages/student/myspace/home/TodaysFocus.tsx
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Compass, Sparkles } from 'lucide-react'
import Card from '../../../../components/ui/Card'
import Badge from '../../../../components/ui/Badge'
import type { NextAction } from './upNext'

const ACCENT: Record<NextAction['urgency'], string> = {
  danger: 'border-l-error',
  warning: 'border-l-warning',
  neutral: 'border-l-secondary',
}
const ICON_TONE: Record<NextAction['urgency'], string> = {
  danger: 'text-error',
  warning: 'text-warning',
  neutral: 'text-secondary',
}
const BADGE: Record<NextAction['urgency'], 'error' | 'warning' | 'neutral'> = {
  danger: 'error',
  warning: 'warning',
  neutral: 'neutral',
}

interface Props {
  action: NextAction | null
  onboardingComplete: boolean
}

/** The single most important action — "one focal point per view" (Spec
 *  2026-06-14 §Modules.1). Caught-up state is positive, never a dead string. */
export default function TodaysFocus({ action, onboardingComplete }: Props) {
  const navigate = useNavigate()

  if (!action) {
    const cta = onboardingComplete
      ? { label: 'Talk to Uni', to: '/s' }
      : { label: 'Keep building your profile', to: '/s/profile' }
    return (
      <Card pad={false} className="border-l-4 border-l-secondary p-5">
        <p className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
          <Sparkles size={15} className="text-secondary" aria-hidden /> You're all caught up
        </p>
        <p className="mt-1 text-xs text-muted-foreground">Nothing urgent right now. A good moment to get ahead.</p>
        <button
          onClick={() => navigate(cta.to)}
          className="ui-btn mt-3 inline-flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"
        >
          <Compass size={13} /> {cta.label}
        </button>
      </Card>
    )
  }

  const Icon = action.icon
  return (
    <Card pad={false} className={`border-l-4 ${ACCENT[action.urgency]} p-5`}>
      <div className="flex items-start gap-3">
        <Icon size={20} className={`mt-0.5 shrink-0 ${ICON_TONE[action.urgency]}`} aria-hidden />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Today's focus</p>
            <Badge variant={BADGE[action.urgency]}>{action.chip}</Badge>
          </div>
          <button
            onClick={() => navigate(action.to)}
            className="mt-1 block text-left text-base font-semibold text-foreground hover:text-secondary"
          >
            {action.title}
          </button>
          <p className="mt-0.5 text-xs text-muted-foreground">{action.sub}</p>
        </div>
        <button
          onClick={() => navigate(action.to)}
          aria-label={`Go: ${action.title}`}
          className="ui-btn mt-0.5 inline-flex shrink-0 items-center gap-1 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"
        >
          Go <ArrowRight size={13} />
        </button>
      </div>
    </Card>
  )
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/student/myspace/home/TodaysFocus.tsx frontend/src/test/myspace-focus.test.tsx
git commit -m "feat(myspace): today's-focus hero"
```

---

### Task 10: Strategy snapshot (`home/StrategySnapshot.tsx`)

**Files:**
- Create: `frontend/src/pages/student/myspace/home/StrategySnapshot.tsx`
- Create: `frontend/src/test/myspace-strategy.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/test/myspace-strategy.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/strategy', () => ({ getActiveStrategy: vi.fn() }))
import { getActiveStrategy } from '../api/strategy'
import StrategySnapshot from '../pages/student/myspace/home/StrategySnapshot'

const strat = vi.mocked(getActiveStrategy)

function renderSnap() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><MemoryRouter><StrategySnapshot /></MemoryRouter></QueryClientProvider>)
}

describe('StrategySnapshot', () => {
  it('shows the career → degree headline for an active strategy', async () => {
    strat.mockResolvedValue({ id: '1', career_target: 'Product Manager', target_degree: "Master's in HCI", narrative: 'Build toward PM via HCI.', is_stub: false } as any)
    renderSnap()
    expect(await screen.findByText(/Product Manager/)).toBeTruthy()
    expect(screen.getByText(/Refine/)).toBeTruthy()
  })
  it('shows the smart-empty CTA when there is no strategy', async () => {
    strat.mockResolvedValue(null)
    renderSnap()
    expect(await screen.findByText(/Shape your path with Uni/i)).toBeTruthy()
  })
  it('treats a stub as empty', async () => {
    strat.mockResolvedValue({ id: '1', career_target: 'x', is_stub: true } as any)
    renderSnap()
    expect(await screen.findByText(/Shape your path with Uni/i)).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run it — Expected: FAIL.**

- [ ] **Step 3: Implement**

```tsx
// frontend/src/pages/student/myspace/home/StrategySnapshot.tsx
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Compass, Route } from 'lucide-react'
import Card from '../../../../components/ui/Card'
import { getActiveStrategy } from '../../../../api/strategy'
import type { StudentStrategy } from '../../../../types'

/** A one-line career → degree snapshot of the active strategy with a Refine
 *  link; smart-empty CTA to Uni when there's no real strategy (Spec
 *  2026-06-14 §Modules.4). Shares the ['strategy','active'] key with StrategyView. */
export default function StrategySnapshot() {
  const navigate = useNavigate()
  const { data, isLoading } = useQuery<StudentStrategy | null>({
    queryKey: ['strategy', 'active'],
    queryFn: () => getActiveStrategy(),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return null
  const real = data && !data.is_stub && (data.career_target || data.target_degree)

  if (!real) {
    return (
      <Card pad={false} className="p-5">
        <p className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
          <Route size={15} className="text-secondary" aria-hidden /> Your strategy
        </p>
        <p className="mt-1 text-xs text-muted-foreground">Shape your path with Uni — a career target sharpens every match and rationale.</p>
        <button
          onClick={() => navigate('/s')}
          className="ui-btn mt-3 inline-flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"
        >
          <Compass size={13} /> Build your strategy
        </button>
      </Card>
    )
  }

  const headline = [data!.career_target, data!.target_degree].filter(Boolean).join(' · ')
  return (
    <Card pad={false} className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            <Route size={13} className="text-secondary" aria-hidden /> Your strategy
          </p>
          <p className="mt-1 truncate text-sm font-semibold text-foreground">{headline}</p>
          {data!.narrative && <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{data!.narrative}</p>}
        </div>
        <button
          onClick={() => navigate('/s/explore?showStrategy=open')}
          className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-secondary hover:underline"
        >
          Refine <ArrowRight size={12} />
        </button>
      </div>
    </Card>
  )
}
```

- [ ] **Step 4: Run it — Expected: PASS.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/student/myspace/home/StrategySnapshot.tsx frontend/src/test/myspace-strategy.test.tsx
git commit -m "feat(myspace): strategy snapshot module"
```

---

### Task 11: Add a gold `tone` to StatTile (earned Offers tile)

`StatTile` hardcodes `text-foreground` on the value, so the earned-gold Offers value needs an opt-in tone. Additive, backward-compatible.

**Files:**
- Modify: `frontend/src/components/student/density/StatTile.tsx`
- Modify: `frontend/src/test/densityComponents.test.tsx`

- [ ] **Step 1: Add a failing test** to `densityComponents.test.tsx` (append inside the file's existing `describe`, matching its render style):

```tsx
it('renders a gold-toned StatTile value when tone="gold"', () => {
  render(<StatTile label="Offers" value={2} tone="gold" />)
  const val = screen.getByText('2')
  expect(val.className).toContain('text-primary')
})
```
(Ensure `StatTile` is imported in that test file; it likely already is. If not, add `import StatTile from '../components/student/density/StatTile'`.)

- [ ] **Step 2: Run it — `npx vitest run src/test/densityComponents.test.tsx` — Expected: FAIL (no `tone` prop; value uses `text-foreground`).**

- [ ] **Step 3: Implement** — add the optional prop:

```tsx
interface StatTileProps {
  label: string
  value: React.ReactNode
  sub?: string
  /** 'gold' tints the value with --primary for an EARNED stat (e.g. an offer
   *  exists). Default leaves it neutral. Gold is reserved for earned moments. */
  tone?: 'default' | 'gold'
}

export default function StatTile({ label, value, sub, tone = 'default' }: StatTileProps) {
  const numeric = typeof value === 'number' && Number.isFinite(value)
  const counted = useCountUp(numeric ? value : 0)
  return (
    <div className="min-w-0">
      <p className={`text-lg font-semibold leading-none ${tone === 'gold' ? 'text-primary' : 'text-foreground'}`}>
        {numeric ? counted : value}
      </p>
      <p className="mt-1 truncate text-eyebrow uppercase text-muted-foreground">{label}</p>
      {sub && <p className="mt-0.5 truncate text-xs text-muted-foreground">{sub}</p>}
    </div>
  )
}
```

- [ ] **Step 4: Run it — Expected: PASS (and no regressions in `densityComponents.test.tsx`).**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/student/density/StatTile.tsx frontend/src/test/densityComponents.test.tsx
git commit -m "feat(density): optional gold tone on StatTile for earned stats"
```

---

### Task 12: Rewire `MySpaceHomePage.tsx` as the composition

Assemble all modules in the focus → momentum → density order; add the strategy query, the earned-gold Offers tile with the one-shot win beat, smart empty states, and `upNext.slice(1)` for the Up-next section.

**Files:**
- Modify: `frontend/src/pages/student/myspace/MySpaceHomePage.tsx`
- Create: `frontend/src/test/myspace-home.test.tsx`

- [ ] **Step 1: Write the smoke test**

```tsx
// frontend/src/test/myspace-home.test.tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../api/applications', () => ({ listMyApplications: vi.fn() }))
vi.mock('../api/calendar', () => ({ getCalendar: vi.fn() }))
vi.mock('../api/saved-lists', () => ({ listSaved: vi.fn() }))
vi.mock('../api/recommendations', () => ({ listRecommendations: vi.fn() }))
vi.mock('../api/workshops-feedback', () => ({ listWorkshopRuns: vi.fn() }))
vi.mock('../api/inbox', () => ({ getThreads: vi.fn() }))
vi.mock('../api/intake', () => ({ listClarifications: vi.fn() }))
vi.mock('../api/students', () => ({ getProfile: vi.fn(), getOnboarding: vi.fn() }))
vi.mock('../api/strategy', () => ({ getActiveStrategy: vi.fn() }))

import { listMyApplications } from '../api/applications'
import { getCalendar } from '../api/calendar'
import { listSaved } from '../api/saved-lists'
import { listRecommendations } from '../api/recommendations'
import { listWorkshopRuns } from '../api/workshops-feedback'
import { getThreads } from '../api/inbox'
import { listClarifications } from '../api/intake'
import { getProfile, getOnboarding } from '../api/students'
import { getActiveStrategy } from '../api/strategy'
import MySpaceHomePage from '../pages/student/myspace/MySpaceHomePage'

beforeEach(() => {
  vi.mocked(listMyApplications).mockResolvedValue([{ id: 'a1', status: 'draft', readiness_pct: 60, program: { program_name: 'CS' } }] as any)
  vi.mocked(getCalendar).mockResolvedValue([])
  vi.mocked(listSaved).mockResolvedValue([{ program_id: 'p1', added_at: new Date().toISOString() }] as any)
  vi.mocked(listRecommendations).mockResolvedValue([])
  vi.mocked(listWorkshopRuns).mockResolvedValue([])
  vi.mocked(getThreads).mockResolvedValue([])
  vi.mocked(listClarifications).mockResolvedValue({ clarifications: [] } as any)
  vi.mocked(getProfile).mockResolvedValue({ first_name: 'Ada' } as any)
  vi.mocked(getOnboarding).mockResolvedValue({ completion_percentage: 50, steps_completed: [], next_step: null } as any)
  vi.mocked(getActiveStrategy).mockResolvedValue(null)
})

function renderHome() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}><MemoryRouter><MySpaceHomePage /></MemoryRouter></QueryClientProvider>)
}

describe('MySpaceHomePage', () => {
  it('renders the greeting, momentum band, pipeline and focus without crashing', async () => {
    renderHome()
    expect(await screen.findByText(/Good (morning|afternoon|evening), Ada/)).toBeTruthy()
    await waitFor(() => expect(screen.getByText('Match')).toBeTruthy()) // journey map
    expect(screen.getByText("Today's focus")).toBeTruthy() // a draft → focus
    expect(screen.getByText('Saved')).toBeTruthy() // pipeline tile
  })
})
```

- [ ] **Step 2: Run it — `npx vitest run src/test/myspace-home.test.tsx` — Expected: FAIL (the page doesn't render the new modules yet).**

- [ ] **Step 3: Rewrite `MySpaceHomePage.tsx`.** Replace the file body with the composition below. It keeps the existing queries + pipeline derivations, drops the deleted `JourneyChecklistCard`, imports the new modules, derives `upNext` via the Task-1 builder, splits it into focus (`[0]`) + rest (`.slice(1)`), adds the strategy snapshot, the earned-gold Offers tile + one-shot beat (`useEffect` + `freshWinIds`/`markCelebrated`), and the smart empties.

```tsx
import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Calendar as CalendarIcon, Mail, FolderKanban, Compass, Target,
  MessageSquare, GraduationCap, ArrowRight,
} from 'lucide-react'
import { PageContainer, PageHeader, SectionHeader, ListRow, StatTile } from '../../../components/student/density'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import { listMyApplications } from '../../../api/applications'
import { getCalendar, type CalendarItem } from '../../../api/calendar'
import { listSaved } from '../../../api/saved-lists'
import { qk } from '../../../api/queryKeys'
import { listRecommendations } from '../../../api/recommendations'
import { listWorkshopRuns } from '../../../api/workshops-feedback'
import { getThreads } from '../../../api/inbox'
import { listClarifications } from '../../../api/intake'
import { getProfile, getOnboarding } from '../../../api/students'
import { useAuthStore } from '../../../stores/auth-store'
import Coachmark from '../../../components/ui/Coachmark'
import { buildUpNext } from './home/upNext'
import TodaysFocus from './home/TodaysFocus'
import MomentumBand from './home/MomentumBand'
import StrategySnapshot from './home/StrategySnapshot'
import { deriveStage } from './home/journeyStage'
import { freshWinIds, markCelebrated } from './home/celebrate'
import type { Application, WorkshopFeedbackRun, OnboardingStatus } from '../../../types'

const STALE = 60_000

function daysUntil(iso: string): number {
  return Math.ceil((new Date(iso).getTime() - Date.now()) / 86_400_000)
}

export default function MySpaceHomePage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()

  const apps = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications, staleTime: STALE })
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile, staleTime: 300_000 })
  const onboarding = useQuery<OnboardingStatus>({ queryKey: ['onboarding'], queryFn: getOnboarding, staleTime: STALE })
  const saved = useQuery({ queryKey: qk.savedPrograms(), queryFn: listSaved, staleTime: STALE })
  const fortnight = useMemo(() => {
    const from = new Date().toISOString().slice(0, 10)
    const to = new Date(Date.now() + 14 * 86_400_000).toISOString().slice(0, 10)
    return { from, to }
  }, [])
  const calendar = useQuery({ queryKey: ['calendar', 'home', fortnight], queryFn: () => getCalendar(fortnight), staleTime: STALE })
  const recs = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations, staleTime: STALE })
  const runs = useQuery({ queryKey: ['workshop-runs', 'home'], queryFn: () => listWorkshopRuns(), staleTime: STALE })
  const threads = useQuery({ queryKey: ['inbox-threads-unread'], queryFn: () => getThreads(), staleTime: 30_000 })
  const clarifications = useQuery({ queryKey: ['intake-clarifications'], queryFn: listClarifications, staleTime: STALE })

  const appList: Application[] = Array.isArray(apps.data) ? apps.data : []
  const savedList: any[] = Array.isArray(saved.data) ? saved.data : []
  const calItems: CalendarItem[] = Array.isArray(calendar.data) ? calendar.data : []
  const recList: any[] = Array.isArray(recs.data) ? recs.data : []
  const runList: WorkshopFeedbackRun[] = (Array.isArray(runs.data) ? runs.data : []).slice().sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
  const threadList: any[] = Array.isArray(threads.data) ? threads.data : []
  const pendingClarifications = clarifications.data?.clarifications?.length ?? 0
  const unreadThreads = threadList.filter(t => t.unread || (t.unread_count ?? 0) > 0).length

  const drafts = appList.filter(a => a.status === 'draft')
  const inFlight = appList.filter(a => ['submitted', 'under_review', 'interview'].includes(a.status))
  const offers = appList.filter(a => a.status === 'decision_made' && ['admitted', 'accepted', 'conditional_admission'].includes(a.decision ?? ''))

  const upNext = buildUpNext({ calItems, offers, drafts, pendingClarifications })
  const focus = upNext[0] ?? null
  const restUpNext = upNext.slice(1)

  const waitingRecs = recList.filter(r => r.status === 'requested')
  const deadlines = calItems.filter(i => i.status !== 'cancelled' && i.status !== 'completed').slice().sort((a, b) => a.start_at.localeCompare(b.start_at)).slice(0, 5)

  // Journey stage + this-week ribbon inputs (real data only).
  const stage = { savedCount: savedList.length, appCount: appList.length, hasOffer: offers.length > 0, hasDecision: appList.some(a => a.status === 'decision_made') }
  const week = { saved: savedList, runs: runList, apps: appList }

  // Earned-gold win beat: a fresh offer fires one gold pulse on the Offers tile.
  const offersEarned = offers.length > 0
  const freshOffer = useMemo(() => freshWinIds(offers.map(o => `offer-${o.id}`)).length > 0, [offers])
  useEffect(() => {
    if (offers.length) markCelebrated(offers.map(o => `offer-${o.id}`))
  }, [offers])

  const anyLoading = apps.isLoading || calendar.isLoading
  const brandNew = !anyLoading && appList.length === 0 && savedList.length === 0
  const onboardingComplete = (onboarding.data?.completion_percentage ?? 0) >= 100

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const firstName = profile.data?.first_name || user?.email?.split('@')[0] || ''

  return (
    <PageContainer>
      <Coachmark
        id="myspace-home"
        title="Your new home base"
        body="Everything personal lives here — applications, prep, calendar, messages, saved programs, and your profile. The rail on the left follows your journey, top to bottom."
        placement="bottom"
      >
        <PageHeader eyebrow="My Space" title={`${greeting}${firstName ? `, ${firstName}` : ''}`} sub="Everything about your applications, in one place" />
      </Coachmark>

      {anyLoading ? (
        <div className="mt-4 space-y-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-40" />
        </div>
      ) : brandNew ? (
        <div className="stagger-list mt-2 space-y-4">
          <MomentumBand stage={stage} week={week} />
          <Card pad={false} className="p-6">
            <p className="text-sm font-medium text-foreground">Your space fills as you work.</p>
            <p className="mt-1 mb-4 text-xs text-muted-foreground">Start with Uni to build your profile, then save programs you like — applications, deadlines and prep will all show up here.</p>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => navigate('/s')} className="ui-btn inline-flex items-center gap-1.5 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground"><Compass size={13} /> Talk to Uni</button>
              <button onClick={() => navigate('/s/explore')} className="ui-btn inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted"><Target size={13} /> Browse matches</button>
            </div>
          </Card>
        </div>
      ) : (
        <div className="stagger-list">
          {/* C — one focal point. */}
          <TodaysFocus action={focus} onboardingComplete={onboardingComplete} />

          {/* A — momentum band. */}
          <MomentumBand stage={stage} week={week} className="mt-5" />

          {/* B — dense dashboard. Pipeline with earned-gold Offers tile. */}
          <div className="mt-5 grid grid-cols-4 gap-3 rounded-lg border border-border bg-card px-4 py-3">
            <button onClick={() => navigate('/s/saved')} className="text-left" aria-label="Saved programs"><StatTile label="Saved" value={savedList.length} /></button>
            <button onClick={() => navigate('/s/applications?status=in_progress')} className="text-left" aria-label="Applications in progress"><StatTile label="In progress" value={drafts.length} /></button>
            <button onClick={() => navigate('/s/applications?status=submitted')} className="text-left" aria-label="Submitted applications"><StatTile label="Submitted" value={inFlight.length} /></button>
            <button
              onClick={() => navigate('/s/applications?tab=offers')}
              aria-label="Offers"
              className={`rounded-md text-left transition-shadow ${offersEarned ? 'ring-1 ring-primary/40 px-2 -mx-2' : ''} ${offersEarned && freshOffer ? 'motion-safe:animate-beat' : ''}`}
            >
              <StatTile label="Offers" value={offers.length} tone={offersEarned ? 'gold' : 'default'} />
            </button>
          </div>

          {/* Up next — everything after the promoted focus. */}
          {restUpNext.length > 0 && (
            <div className="stagger-list mt-5">
              <SectionHeader>Up next</SectionHeader>
              {restUpNext.map(a => (
                <ListRow
                  key={a.key}
                  media={<a.icon size={15} className={a.urgency === 'danger' ? 'text-error' : a.urgency === 'warning' ? 'text-warning' : 'text-muted-foreground'} />}
                  title={a.title}
                  sub={a.sub}
                  trailing={<Badge variant={a.urgency === 'danger' ? 'error' : a.urgency === 'warning' ? 'warning' : 'neutral'}>{a.chip}</Badge>}
                  onClick={() => navigate(a.to)}
                />
              ))}
            </div>
          )}

          <div className="mt-5 grid gap-6 md:grid-cols-2">
            {/* Deadlines — next 14 days */}
            <div>
              <SectionHeader action={<button onClick={() => navigate('/s/calendar')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline">Calendar <ArrowRight size={12} /></button>}>Deadlines · next 14 days</SectionHeader>
              {calendar.isError ? (
                <p className="py-2 text-sm text-muted-foreground">Couldn't load your calendar.</p>
              ) : deadlines.length === 0 ? (
                <p className="py-2 text-sm text-muted-foreground">Nothing due in the next two weeks — a good time to get ahead in <button className="text-secondary hover:underline" onClick={() => navigate('/s/prep')}>Prep</button>.</p>
              ) : (
                deadlines.map(item => {
                  const d = daysUntil(item.start_at)
                  return (
                    <ListRow
                      key={item.id}
                      title={item.title}
                      sub={item.subtitle ?? item.institution_name ?? undefined}
                      trailing={<span className={`text-xs ${d <= 3 ? 'text-error font-medium' : 'text-muted-foreground'}`}>{new Date(item.start_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>}
                      onClick={() => navigate('/s/calendar')}
                    />
                  )
                })
              )}
            </div>

            {/* Waiting on others + latest feedback */}
            <div>
              <SectionHeader>Waiting on others</SectionHeader>
              {waitingRecs.length === 0 ? (
                <p className="py-2 text-sm text-muted-foreground">No pending requests. When you ask for a recommendation it'll show here — <button className="text-secondary hover:underline" onClick={() => navigate('/s/prep?tab=recommenders')}>request a letter</button>.</p>
              ) : (
                waitingRecs.slice(0, 3).map(r => (
                  <ListRow
                    key={r.id}
                    media={<Mail size={15} className="text-muted-foreground" />}
                    title={`Rec letter — ${r.recommender_name}`}
                    sub={r.requested_at ? `Requested ${new Date(r.requested_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}` : 'Requested'}
                    trailing={<Badge variant="neutral">waiting</Badge>}
                    onClick={() => navigate('/s/prep?tab=recommenders')}
                  />
                ))
              )}

              <div className="mt-4">
                <SectionHeader action={unreadThreads > 0 ? <button onClick={() => navigate('/s/messages')} className="inline-flex items-center gap-1 text-xs text-secondary hover:underline"><MessageSquare size={12} /> {unreadThreads} unread</button> : undefined}>Latest feedback</SectionHeader>
                {runList.length === 0 ? (
                  <p className="py-2 text-sm text-muted-foreground">No workshop runs yet — get feedback on an essay draft in <button className="text-secondary hover:underline" onClick={() => navigate('/s/prep?tab=workshops')}>Prep</button>.</p>
                ) : (
                  runList.slice(0, 3).map(run => (
                    <ListRow
                      key={run.id}
                      media={<GraduationCap size={15} className="text-muted-foreground" />}
                      title={`${run.domain === 'essay' ? 'Essay' : run.domain === 'interview' ? 'Interview' : 'Test'} feedback`}
                      sub={new Date(run.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      onClick={() => navigate('/s/prep?tab=workshops')}
                    />
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Strategy snapshot — its own row. */}
          <div className="mt-5">
            <StrategySnapshot />
          </div>

          <div className="mt-6 flex justify-end">
            <button onClick={() => navigate('/s/applications')} className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"><FolderKanban size={12} /> All applications <ArrowRight size={12} /></button>
          </div>
        </div>
      )}
    </PageContainer>
  )
}
```

- [ ] **Step 4: Run it — `npx vitest run src/test/myspace-home.test.tsx` — Expected: PASS.**

- [ ] **Step 5: Verify — `npx tsc -p tsconfig.app.json --noEmit` (0 errors).** If `OnboardingStatus` isn't exported from `types`, import it from where `getOnboarding` types it (check `api/students.ts`); adjust the import to match the real export site.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/student/myspace/MySpaceHomePage.tsx frontend/src/test/myspace-home.test.tsx
git commit -m "feat(myspace): compose home — focus · momentum · density"
```

---

### Task 13: Full verification

- [ ] **Typecheck + build:** `cd frontend && npx tsc -p tsconfig.app.json --noEmit && npm run build` — 0 errors, build succeeds.
- [ ] **All new + adjacent tests:** `npx vitest run src/test/myspace-upnext.test.ts src/test/myspace-week.test.ts src/test/myspace-stage.test.ts src/test/myspace-celebrate.test.ts src/test/myspace-journeymap.test.tsx src/test/myspace-weekribbon.test.tsx src/test/myspace-momentum.test.tsx src/test/myspace-focus.test.tsx src/test/myspace-strategy.test.tsx src/test/myspace-home.test.tsx src/test/densityComponents.test.tsx` — all green.
- [ ] **Full suite:** `npx vitest run` — green (no regressions; confirm nothing imported the deleted `JourneyChecklistCard`: `grep -rn "JourneyChecklistCard" src` returns nothing).
- [ ] **Lint:** `npx eslint src/pages/student/myspace src/components/student/density/StatTile.tsx --max-warnings=0` — clean.
- [ ] **iCloud dup purge:** `git ls-files | grep ' 2\.'` empty.

### Task 14: Visual verification + ship

- [ ] **Live preview** (isolated seed DB; recipe in memory `project_student_qa_aj_and_preview_recipe`): worktree uvicorn + vite, repointed `launch.json` + `VITE_API_URL`. Verify two personas:
  - Sparse student: Today's focus shows a setup/Uni caught-up state or top draft; MomentumBand ring visible (< 100%), journey at Discover/Match; week ribbon smart-empty; smart empties in Deadlines/Waiting; strategy snapshot CTA.
  - Busy student: offers present → Offers tile gold + one beat (once); journey at Decide; ribbon populated; ring hidden at 100%.
  - Check desktop + mobile (≤ `lg`) + dark mode + reduced-motion (no count-ups/beats, content still correct).
- [ ] **Screenshot** both personas for the user.
- [ ] **Ship (standing rule):** push `claude/myspace-redesign`, open a PR to `main`, wait for CI green, squash-merge, confirm S3+CloudFront frontend deploy, verify the live bundle (`curl -s https://app.unipaith.co/assets/index-*.js | grep -o "Today's focus"` → hit; `grep -o "quiet week"` → hit). Confirm working tree clean + `main` at the new commit.

---

## Self-review

- **Spec coverage:** §Layout 1–8 → Tasks 9 (focus), 8 (momentum), 12 (pipeline/up-next/deadlines/waiting/strategy/footer); §Modules.1 → T9; §Modules.2a ring → T5+T8; §2b journey map → T3+T6; §2c ribbon → T2+T7; §3 pipeline count-up+gold → T11+T12; §4 strategy → T10; §5 smart empties → T12; §6 win beat → T4+T12; §Motion → PageContainer/stagger kept in T12, count-ups via StatTile/ProgressRing, beat in T12; §File structure → Tasks create exactly the listed `home/*` files + delete JourneyChecklistCard (T8); §Testing → each module has a test, smoke in T12, full run T13; §Visual + Cleanup → T14.
- **Placeholder scan:** none — every code step shows full code; commands have expected output.
- **Type consistency:** `NextAction`/`buildUpNext`/`UpNextInputs` (T1) reused by T9+T12; `StageInputs`/`deriveStage`/`STAGES`/`stageIndex` (T3) by T6+T12; `WeekInputs`/`countThisWeek`/`WeekCounts` (T2) by T7+T12; `freshWinIds`/`markCelebrated` (T4) by T12; `ProgressRing` default export (T5) by T8; `MomentumBand` props `{stage, week, className}` (T8) match T12 call; `StatTile` `tone` (T11) used in T12; `TodaysFocus` props `{action, onboardingComplete}` (T9) match T12.
- **Risk flagged inline:** T12 Step 5 — confirm the real export site of `OnboardingStatus` before relying on the `types` import.
