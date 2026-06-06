# Student-side UI Densification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, user pre-authorized autonomous execution + push). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shift all ~17 student surfaces to a denser, LinkedIn-like "app" feel via a shared density component layer + a per-surface densification recipe, without re-architecting layouts.

**Architecture:** 4 new shared presentational components in `frontend/src/components/student/density/` (`PageHeader`, `SectionHeader`, `ListRow`, `StatTile`) that encode the rubric (tight rhythm, compact rows, surfaced counts, utilitarian headers). Each surface is then refactored to use them + kill dead whitespace. All use existing semantic tokens — no new colors. Each wave = a fresh-branch-off-latest-`main` PR, screenshot-verified + tests green, pushed autonomously.

**Tech Stack:** React 19 + TypeScript + Vite + Tailwind, Vitest + Testing Library, ESLint, tsc.

---

## File structure

- Create `frontend/src/components/student/density/PageHeader.tsx` — compact page header (eyebrow + small heading + count + right actions).
- Create `frontend/src/components/student/density/SectionHeader.tsx` — small uppercase eyebrow label + count + optional action.
- Create `frontend/src/components/student/density/ListRow.tsx` — dense list row (optional media, title + subline, trailing slot; hairline divider, hover).
- Create `frontend/src/components/student/density/StatTile.tsx` — compact stat (value + label + optional sub).
- Create `frontend/src/components/student/density/index.ts` — barrel export.
- Create `frontend/src/test/densityComponents.test.tsx` — render tests for all four.
- Modify `CLAUDE.md` — "UI/Design Preferences" block.
- Modify (waves, per surface): `DiscoverHomePage`, `ExplorePage`, `ManagementPage`/`ApplicationsPage`/`CalendarPage`/`MessagesPage`, `ProgramDetailPage`, `InstitutionDetailPage`, `SchoolSubunitPage`, `ProfilePage`, `PostsPage`, `SavedListPage`, `SettingsPage`, `RecommendationsPage`, `FinancialAidPage`, `OnboardingPage`.

**Before creating components:** grep `frontend/src/components/ui/` + existing pages for any current `PageHeader`/`SectionHeader`/list-row/stat patterns. If a close equivalent exists, extend it instead of duplicating (DRY). The code below is the target shape; align class names to the existing token utilities.

---

## PR 0 — The density layer

### Task 1: SectionHeader

**Files:**
- Create: `frontend/src/components/student/density/SectionHeader.tsx`
- Test: `frontend/src/test/densityComponents.test.tsx`

- [ ] **Step 1: Write the failing test** (in `densityComponents.test.tsx`)

```tsx
import { render, screen } from '@testing-library/react'
import { SectionHeader } from '../components/student/density'

test('SectionHeader renders label + count', () => {
  render(<SectionHeader count={5}>Recently viewed</SectionHeader>)
  expect(screen.getByText('Recently viewed')).toBeInTheDocument()
  expect(screen.getByText('5')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run it to confirm it fails** — `cd frontend && node_modules/.bin/vitest run src/test/densityComponents.test.tsx` → FAIL (module not found).

- [ ] **Step 3: Implement** `SectionHeader.tsx`:

```tsx
interface SectionHeaderProps {
  children: React.ReactNode
  count?: number
  action?: React.ReactNode
  className?: string
}

export default function SectionHeader({ children, count, action, className = '' }: SectionHeaderProps) {
  return (
    <div className={`flex items-center justify-between gap-2 mb-2 ${className}`}>
      <h2 className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {children}
        {count != null && <span className="ml-1.5 text-muted-foreground/70">{count}</span>}
      </h2>
      {action}
    </div>
  )
}
```

- [ ] **Step 4:** Add to barrel `index.ts`: `export { default as SectionHeader } from './SectionHeader'` (create the others' exports as they're added).
- [ ] **Step 5: Run test** → PASS.

### Task 2: PageHeader

- [ ] **Step 1: Test:**

```tsx
import PageHeaderTest from '../components/student/density/PageHeader' // or via barrel
test('PageHeader renders eyebrow, title, count, sub', () => {
  render(<PageHeader eyebrow="Match" title="Your matches" count={12} sub="Ranked for fit" />)
  expect(screen.getByText('Match')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: /Your matches/ })).toBeInTheDocument()
  expect(screen.getByText('12')).toBeInTheDocument()
})
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: Implement** `PageHeader.tsx`:

```tsx
interface PageHeaderProps {
  eyebrow?: string
  title: string
  count?: number
  sub?: string
  actions?: React.ReactNode
}

export default function PageHeader({ eyebrow, title, count, sub, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-3 mb-3">
      <div className="min-w-0">
        {eyebrow && <p className="text-[11px] font-semibold uppercase tracking-wide text-secondary mb-0.5">{eyebrow}</p>}
        <h1 className="text-lg font-semibold leading-tight text-foreground">
          {title}
          {count != null && <span className="ml-2 text-sm font-normal text-muted-foreground">{count}</span>}
        </h1>
        {sub && <p className="mt-0.5 text-[13px] text-muted-foreground">{sub}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}
```

- [ ] **Step 4:** barrel export. **Step 5:** run → PASS.

### Task 3: ListRow

- [ ] **Step 1: Test:**

```tsx
import { ListRow } from '../components/student/density'
test('ListRow renders title + sub + trailing, fires onClick', () => {
  const onClick = vi.fn()
  render(<ListRow title="Computer Science" sub="MIT · MS" trailing={<span>›</span>} onClick={onClick} />)
  expect(screen.getByText('Computer Science')).toBeInTheDocument()
  expect(screen.getByText('MIT · MS')).toBeInTheDocument()
  screen.getByRole('button').click()
  expect(onClick).toHaveBeenCalled()
})
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: Implement** `ListRow.tsx`:

```tsx
interface ListRowProps {
  media?: React.ReactNode
  title: React.ReactNode
  sub?: React.ReactNode
  trailing?: React.ReactNode
  onClick?: () => void
}

export default function ListRow({ media, title, sub, trailing, onClick }: ListRowProps) {
  const interactive = !!onClick
  const Tag = interactive ? 'button' : 'div'
  return (
    <Tag
      {...(interactive ? { type: 'button' as const, onClick } : {})}
      className={`flex w-full items-center gap-3 border-b border-border py-2 text-left last:border-0 ${
        interactive ? '-mx-2 rounded-md px-2 transition-colors hover:bg-muted/50' : ''
      }`}
    >
      {media && <span className="shrink-0">{media}</span>}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-foreground">{title}</span>
        {sub && <span className="block truncate text-xs text-muted-foreground">{sub}</span>}
      </span>
      {trailing && <span className="shrink-0">{trailing}</span>}
    </Tag>
  )
}
```

- [ ] **Step 4:** barrel export. **Step 5:** run → PASS.

### Task 4: StatTile

- [ ] **Step 1: Test:**

```tsx
import { StatTile } from '../components/student/density'
test('StatTile renders value + label', () => {
  render(<StatTile value={3} label="In progress" />)
  expect(screen.getByText('3')).toBeInTheDocument()
  expect(screen.getByText('In progress')).toBeInTheDocument()
})
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3: Implement** `StatTile.tsx`:

```tsx
interface StatTileProps {
  label: string
  value: React.ReactNode
  sub?: string
}

export default function StatTile({ label, value, sub }: StatTileProps) {
  return (
    <div className="min-w-0">
      <p className="text-lg font-semibold leading-none text-foreground">{value}</p>
      <p className="mt-1 truncate text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      {sub && <p className="mt-0.5 truncate text-xs text-muted-foreground">{sub}</p>}
    </div>
  )
}
```

- [ ] **Step 4:** barrel export. **Step 5:** run all four tests → PASS.

### Task 5: CLAUDE.md update + ship PR 0

- [ ] **Step 1:** In `CLAUDE.md` "## UI/Design Preferences", replace the editorial-restraint bullets with: dense/utilitarian/app-like (LinkedIn-leaning) within existing layouts; surfaced metadata + counts; compact rows; **keep** "NO decorative images, gradients, or color accents".
- [ ] **Step 2:** `cd frontend && node_modules/.bin/tsc -b && node_modules/.bin/eslint src/components/student/density src/test/densityComponents.test.tsx && node_modules/.bin/vitest run` → all green.
- [ ] **Step 3:** Commit + push + PR + merge (fresh branch already = `claude/ux-densification`).

---

## Waves A / B / C — per-surface densification recipe

The per-surface work is visual refactoring; the "test" is **the existing vitest suite stays green** + **a live screenshot shows higher density with nothing broken**. For EACH surface in the wave:

- [ ] **Step 1:** Read the surface file. Identify: the page header block, any stat strip, the main list(s), and empty/low-density regions.
- [ ] **Step 2:** Apply the recipe:
  - Replace the bespoke page header with `<PageHeader eyebrow title count sub actions />`.
  - Replace bespoke section labels with `<SectionHeader count action>`.
  - Replace tall bordered "pill" lists with `<ListRow>` lists (≈50% denser).
  - Replace stat strips with a compact `<StatTile>` row.
  - Cut oversized vertical gaps (`space-y-8`→`space-y-4`, `mb-8`→`mb-4`, `p-6`→`p-4` where it reads loose); surface counts; fill obvious dead whitespace.
  - Do **not** touch loading/error-state or a11y code (parallel session's lane).
- [ ] **Step 3:** `node_modules/.bin/tsc -b && node_modules/.bin/eslint <files> && node_modules/.bin/vitest run` → green.
- [ ] **Step 4:** Live screenshot the surface (logged in as the demo student) → confirm denser + intact.
- [ ] **Step 5:** Commit. At the end of the wave: push + PR + merge (fresh branch off latest `main`).

**Wave A:** `DiscoverHomePage.tsx`, `ExplorePage.tsx`, `ManagementPage.tsx` (+ `ApplicationsPage.tsx`, `CalendarPage.tsx`, `MessagesPage.tsx`).
**Wave B:** `ProgramDetailPage.tsx`, `InstitutionDetailPage.tsx`, `SchoolSubunitPage.tsx`, `ProfilePage.tsx`.
**Wave C:** `PostsPage.tsx`, `SavedListPage.tsx`, `SettingsPage.tsx`, `RecommendationsPage.tsx`, `FinancialAidPage.tsx`, `OnboardingPage.tsx`.

---

## Self-review

- **Spec coverage:** rubric rules 1–6 → encoded in the 4 components (1,2,4,6) + the recipe (1,3,5); mechanism → density layer; rollout → PR 0 + Waves A/B/C; docs → Task 5; validation → recipe Steps 3–4. All covered.
- **Placeholders:** PR 0 tasks have complete component + test code. Wave tasks are an explicit recipe (per-surface code is discovered by reading each file — appropriate for a systematic visual refactor; not a placeholder).
- **Type consistency:** component prop names (`eyebrow`, `title`, `count`, `sub`, `actions`, `media`, `trailing`, `value`, `label`) are consistent across tasks + the barrel.
