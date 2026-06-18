/**
 * "Your plan" — a connected Planning overview, folded into the TOP of the
 * Strategy tab (Spec 2026-06-18 — planning-that-connects).
 *
 * Planning is four disconnected CRUD tabs (Strategy · Goals · Needs ·
 * Preferences); the dependencies between them are invisible. This overview
 * makes the "feeds into" relationships explicit:
 *
 *   Goals → Strategy → Needs & prefs → Matches
 *
 * Two parts:
 *  1. The chain — four compact nodes left-to-right, each a live count + hint;
 *     clicking deep-links to that piece. Strategy is the "you are here" anchor.
 *  2. Sharpen your plan — a derived list of ONLY the real gaps (each a one-tap
 *     link). Hides entirely when nothing applies (no invented gap, no pep line).
 *
 * Frontend-only. Composes existing endpoints client-side, reusing the SHARED
 * TanStack Query keys so the cache dedupes with the rest of the app (the
 * StrategyTab below already fetches ['strategy','active']).
 */
import type { ComponentType } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Route, SlidersHorizontal, Sparkles, Target } from 'lucide-react'

import { SectionHeader } from '../../../../components/student/density'
import { getActiveStrategy } from '../../../../api/strategy'
import { listGoals } from '../../../../api/goals'
import { listNeeds } from '../../../../api/needs'
import { getPreferences } from '../../../../api/students'
import { getMatches } from '../../../../api/matching'
import type { MatchResultDual, StudentGoal, StudentNeed, StudentStrategy } from '../../../../types'

/** Fitness arrives as a string|number that may be null/'' (Phase A). Normalize
 *  to a 0..1 unit the same way TopMatchesPeek/MatchCard do. */
function toUnit(v: string | number | null | undefined): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? 0)
  if (!Number.isFinite(n)) return 0
  const u = n > 1 ? n / 100 : n
  return Math.max(0, Math.min(1, u))
}

/** A preferences object is "set" if any of budget_max / funding_requirement /
 *  a non-empty preferred_countries is present. */
function preferencesAreSet(prefs: unknown): boolean {
  if (!prefs || typeof prefs !== 'object') return false
  const p = prefs as Record<string, unknown>
  const countries = p.preferred_countries
  const hasCountries = Array.isArray(countries) && countries.length > 0
  return (
    p.budget_max != null ||
    Boolean(p.funding_requirement) ||
    hasCountries
  )
}

interface ChainNodeProps {
  icon: ComponentType<{ size?: number; className?: string }>
  label: string
  value: string
  sub?: string
  /** The center anchor (current tab) renders as a marked, non-interactive node. */
  anchor?: boolean
  onClick?: () => void
}

function ChainNode({ icon: Icon, label, value, sub, anchor, onClick }: ChainNodeProps) {
  const accent = anchor ? 'text-secondary' : 'text-muted-foreground'
  const inner = (
    <>
      <Icon size={14} className={`shrink-0 ${accent}`} aria-hidden="true" />
      <span className="min-w-0">
        <span className="block text-eyebrow uppercase text-muted-foreground">{label}</span>
        <span className="mt-0.5 block truncate text-sm font-semibold text-foreground">{value}</span>
        {sub && <span className="mt-0.5 block truncate text-xs text-muted-foreground">{sub}</span>}
      </span>
    </>
  )
  if (anchor) {
    return (
      <div
        className="flex w-full items-start gap-2 rounded-lg border border-secondary/40 bg-card px-3 py-2.5 ring-1 ring-secondary/20"
        aria-current="page"
      >
        {inner}
      </div>
    )
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-start gap-2 rounded-lg border border-border bg-muted px-3 py-2.5 text-left transition-colors hover:bg-muted/70"
    >
      {inner}
    </button>
  )
}

interface Gap {
  label: string
  to: string
}

export default function PlanOverview() {
  const navigate = useNavigate()

  const { data: strategy, isLoading: strategyLoading } = useQuery<StudentStrategy | null>({
    queryKey: ['strategy', 'active'],
    queryFn: () => getActiveStrategy(),
  })
  const { data: goals, isLoading: goalsLoading } = useQuery<StudentGoal[]>({
    queryKey: ['goals'],
    queryFn: () => listGoals(),
  })
  const { data: needs, isLoading: needsLoading } = useQuery<StudentNeed[]>({
    queryKey: ['needs'],
    queryFn: () => listNeeds(),
  })
  const { data: preferences, isLoading: prefsLoading } = useQuery({
    queryKey: ['preferences'],
    queryFn: () => getPreferences(),
  })
  const { data: matches } = useQuery<MatchResultDual[]>({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    retry: 1,
  })

  // While the core queries load, render nothing (the StrategyTab below shows
  // its own loading state). Matches is best-effort and excluded from the gate.
  if (strategyLoading || goalsLoading || needsLoading || prefsLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[0, 1, 2, 3].map(i => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    )
  }

  // Guard everything against null/empty data.
  const goalList = goals ?? []
  const needList = needs ?? []
  const matchList = matches ?? []

  const activeGoals = goalList.filter(g => g.status === 'active')
  const academicGoals = activeGoals.filter(g => g.category === 'academic')
  const needsCount = needList.length
  const mustHaves = needList.filter(n => n.severity === 'must_have').length
  const prefsSet = preferencesAreSet(preferences)

  const matchCount = matchList.length
  const fits = matchList
    .filter(m => m.fitness_score != null && m.fitness_score !== '')
    .map(m => Math.round(toUnit(m.fitness_score) * 100))
  const topFit = fits.length > 0 ? Math.max(...fits) : null

  // Strategy node summary.
  const hasStrategy = Boolean(strategy)
  const strategyValue = strategy
    ? `v${strategy.version}`
    : 'None yet'
  const strategyHeadline = strategy
    ? [strategy.career_target, strategy.target_degree].filter(Boolean).join(' → ') || 'In progress'
    : undefined
  const strategySub = strategy
    ? strategy.is_stub
      ? strategyHeadline
        ? `${strategyHeadline} · preview`
        : 'Preview'
      : strategyHeadline
    : 'Generate from a goal'

  // Needs & prefs node sub: must-haves + whether preferences are set.
  const needsSub = `${mustHaves} must-have${mustHaves === 1 ? '' : 's'} · ${prefsSet ? 'preferences set' : 'preferences incomplete'}`

  // Derive only the gaps that actually apply (show-don't-tell).
  const gaps: Gap[] = []
  if (academicGoals.length === 0) {
    gaps.push({ label: 'Add an academic goal to generate a strategy', to: '/s/profile?tab=goals' })
  }
  if (!hasStrategy || strategy?.is_stub) {
    gaps.push({ label: 'Your strategy is a preview — develop it with Uni', to: '/s?intent=strategy' })
  }
  if (needsCount === 0) {
    gaps.push({ label: 'Map what you need to sharpen matches', to: '/s/profile?tab=needs' })
  }
  if (!prefsSet) {
    gaps.push({ label: 'Set your preferences to sharpen matches', to: '/s/profile?tab=preferences' })
  }
  if (activeGoals.length > 0 && academicGoals.length === activeGoals.length) {
    gaps.push({ label: 'Add a social or personal goal', to: '/s/profile?tab=goals' })
  }

  return (
    <section className="rounded-xl border border-border bg-card p-4">
      <SectionHeader>Your plan</SectionHeader>

      {/* The chain — Goals → Strategy → Needs & prefs → Matches. */}
      <div className="flex flex-col gap-2 lg:flex-row lg:items-stretch">
        <div className="flex-1">
          <ChainNode
            icon={Target}
            label="Goals"
            value={`${activeGoals.length} active`}
            sub={`${academicGoals.length} academic`}
            onClick={() => navigate('/s/profile?tab=goals')}
          />
        </div>
        <ChainArrow />
        <div className="flex-1">
          <ChainNode
            icon={Route}
            label="Strategy"
            value={strategyValue}
            sub={strategySub}
            anchor
          />
        </div>
        <ChainArrow />
        <div className="flex-1">
          <ChainNode
            icon={SlidersHorizontal}
            label="Needs & prefs"
            value={`${needsCount} need${needsCount === 1 ? '' : 's'}`}
            sub={needsSub}
            onClick={() => navigate('/s/profile?tab=needs')}
          />
        </div>
        <ChainArrow />
        <div className="flex-1">
          <ChainNode
            icon={Sparkles}
            label="Matches"
            value={matchCount > 0 ? `${matchCount}` : 'None yet'}
            sub={topFit != null ? `top ${topFit}% fit` : undefined}
            onClick={() => navigate('/s/explore')}
          />
        </div>
      </div>

      <p className="mt-2 text-xs text-muted-foreground">
        Goals shape your strategy. Your needs &amp; preferences shape your matches.
      </p>

      {/* Sharpen your plan — only the gaps that actually apply. */}
      {gaps.length > 0 && (
        <div className="mt-4 border-t border-border pt-4">
          <SectionHeader>Sharpen your plan</SectionHeader>
          <ul className="divide-y divide-border">
            {gaps.map(gap => (
              <li key={gap.label}>
                <button
                  type="button"
                  onClick={() => navigate(gap.to)}
                  className="-mx-2 flex w-full items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-muted/50"
                >
                  <span className="min-w-0 flex-1 truncate text-sm text-foreground">{gap.label}</span>
                  <ArrowRight size={14} className="shrink-0 text-muted-foreground" aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

/** A directional connector between chain nodes — horizontal on lg+, where the
 *  flow reads left-to-right; vertical (rotated) when the nodes stack. */
function ChainArrow() {
  return (
    <div className="flex items-center justify-center self-center lg:px-0.5" aria-hidden="true">
      <ArrowRight size={16} className="rotate-90 text-muted-foreground lg:rotate-0" />
    </div>
  )
}
