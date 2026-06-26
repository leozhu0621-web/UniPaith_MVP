/**
 * Phase C — Strategy view at the top of /s/explore.
 *
 * Renders the active broad-strategy artifact above the search/browse area
 * so the student lands on Strategy first (per spec). Three states:
 *   1. No active strategy + no goals → empty CTA pointing back to Discover
 *   2. No active strategy + goals exist → "Generate strategy" button
 *   3. Active strategy → sectioned summary (career → degree → paths)
 *
 * Collapsible so power users who skim straight to programs can hide it.
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  Compass,
  Pencil,
  RefreshCw,
  Sparkles,
  Target,
} from 'lucide-react'

import { listGoals } from '../../../api/goals'
import { activateStrategy, generateStrategy, getActiveStrategy } from '../../../api/strategy'
import { formatRelative } from '../../../utils/format'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import type { StudentGoal, StudentStrategy } from '../../../types'

const COLLAPSED_KEY = 'unipaith.match-strategy-collapsed'

export default function StrategyView({ forceExpanded = false }: { forceExpanded?: boolean }) {
  const qc = useQueryClient()
  const [collapsed, setCollapsed] = useState(() => {
    if (forceExpanded) return false
    return typeof window !== 'undefined' && window.localStorage.getItem(COLLAPSED_KEY) === '1'
  })

  useEffect(() => {
    if (forceExpanded) setCollapsed(false)
  }, [forceExpanded])

  const {
    data: strategy,
    isLoading: strategyLoading,
    isError: strategyError,
    refetch: refetchStrategy,
  } = useQuery<StudentStrategy | null>({
    queryKey: ['strategy', 'active'],
    queryFn: () => getActiveStrategy(),
  })
  // Only fetch goals when there's no active strategy — saves a roundtrip
  // on the happy path. Skip while the strategy fetch is errored so we don't
  // fall through to a misleading "no goals" empty state on a transient failure.
  const { data: goals = [] } = useQuery<StudentGoal[]>({
    queryKey: ['goals', 'active'],
    queryFn: () => listGoals('active'),
    enabled: !strategy && !strategyError,
  })
  // The backend requires at least one ACADEMIC goal to generate a strategy
  // (strategy_service raises 400 otherwise), so gate the CTA on that — not on
  // any active goal — or a student with only social/personal goals sees an
  // enabled "Generate strategy" button that errors on click.
  const academicGoals = goals.filter((g) => g.category === 'academic')

  // Spec 09 §3 / §12 — "Generate" (no active yet) and "Regenerate" (refresh the
  // active) both produce a *visible* active strategy: generate the new version,
  // then promote it so the card updates in place. (The separate "Edit" path
  // intentionally creates a draft for review without activating.)
  const generateMut = useMutation({
    mutationFn: async () => {
      const next = await generateStrategy()
      return activateStrategy(next.id)
    },
    onSuccess: () => {
      showToast(strategy ? 'Strategy regenerated.' : 'Strategy generated.', 'success')
      qc.invalidateQueries({ queryKey: ['strategy'] })
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not generate strategy.', 'error'),
  })

  const toggle = () => {
    const next = !collapsed
    setCollapsed(next)
    window.localStorage.setItem(COLLAPSED_KEY, next ? '1' : '0')
  }

  if (strategyLoading) {
    return (
      <Card>
        <div className="space-y-2.5">
          <Skeleton className="h-4 w-44" />
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </Card>
    )
  }

  // Fetch failed → show a retry instead of falling through to a misleading
  // "no strategy / no goals" empty state (Spec 78 §3).
  if (strategyError) {
    return (
      <Card>
        <QueryError
          variant="inline"
          title="We couldn't load your strategy."
          onRetry={() => refetchStrategy()}
        />
      </Card>
    )
  }

  // State 1 — no goals at all → push student back to Discover.
  if (!strategy && academicGoals.length === 0) {
    return (
      <Card className="bg-muted border-border">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <Compass size={18} className="text-secondary mt-0.5 shrink-0" />
            <div>
              <div className="text-sm font-medium text-foreground">
                Tell me about you first.
              </div>
            </div>
          </div>
          <Link to="/s">
            <Button size="sm">Talk to Uni</Button>
          </Link>
        </div>
      </Card>
    )
  }

  // State 2 — goals exist but no active strategy → offer to generate.
  if (!strategy) {
    return (
      <Card className="bg-muted border-border">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <Sparkles size={18} className="text-secondary mt-0.5 shrink-0" />
            <div>
              <div className="text-sm font-medium text-foreground">
                Ready to plan your strategy.
              </div>
              <div className="text-xs text-foreground mt-1">
                You have {academicGoals.length} academic goal{academicGoals.length === 1 ? '' : 's'}.
              </div>
            </div>
          </div>
          <Button
            size="sm"
            onClick={() => generateMut.mutate()}
            loading={generateMut.isPending}
          >
            Generate strategy
          </Button>
        </div>
      </Card>
    )
  }

  // State 3 — active strategy (Spec 09 §3 + §2 five-line layout).
  const academic = summarizePath(strategy.academic_path.map(s => s.step))
  const financial = summarizePath(strategy.financial_path.map(f => f.aid_type))
  const geographic = summarizePath(strategy.geographic_path.map(g => g.region))

  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <button
          className="flex items-center gap-2 text-left"
          onClick={toggle}
          aria-expanded={!collapsed}
        >
          {collapsed ? (
            <ChevronRight size={14} className="text-foreground" />
          ) : (
            <ChevronDown size={14} className="text-foreground" />
          )}
          <Target size={16} className="text-secondary" />
          <div>
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Active strategy · v{strategy.version}{strategy.generated_at ? ` · ${formatRelative(strategy.generated_at)}` : ''}
            </div>
            <div className="text-base font-semibold text-foreground">
              {strategy.career_target ?? 'Strategy'}
              {strategy.target_degree && (
                <span className="text-sm text-foreground font-normal">
                  {' '}
                  → {strategy.target_degree}
                </span>
              )}
            </div>
          </div>
        </button>
        {strategy.is_stub && (
          <Badge variant="warning" size="sm" className="inline-flex items-center gap-1 shrink-0">
            <Sparkles size={10} />
            preview
          </Badge>
        )}
      </div>

      {/* Spec 09 §3 — on regenerate failure, preserve the existing strategy
          and surface an inline banner (never blank the card). */}
      {generateMut.isError && (
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-warning/30 bg-warning-soft px-3 py-2 text-xs text-foreground">
          <AlertCircle size={13} className="mt-0.5 shrink-0 text-warning" />
          Couldn&apos;t regenerate your strategy. Showing your current one.
        </div>
      )}

      {!collapsed && (
        <>
          <div className="mt-4 space-y-2">
            <StrategyLine label="Career path" value={strategy.career_target} />
            <StrategyLine label="Degree path" value={strategy.target_degree} />
            <StrategyLine label="Academic" value={academic} />
            <StrategyLine label="Financial" value={financial} />
            <StrategyLine label="Geographic" value={geographic} />
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="tertiary"
              onClick={() => generateMut.mutate()}
              loading={generateMut.isPending}
            >
              <RefreshCw size={13} className="mr-1.5" />
              Regenerate strategy
            </Button>
            <Link to="/s/profile?tab=strategy">
              <Button size="sm" variant="ghost">
                <Pencil size={13} className="mr-1.5" />
                Edit (creates a draft)
              </Button>
            </Link>
            <Link
              to="/s/profile?tab=strategy"
              className="inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:underline ml-auto"
            >
              Open full strategy
              <ArrowRight size={12} />
            </Link>
          </div>
        </>
      )}
    </Card>
  )
}

/** One labeled line of the active-strategy summary (Spec 09 §2 ASCII). */
function StrategyLine({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex items-baseline gap-3">
      <span className="w-24 shrink-0 text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="text-sm text-foreground min-w-0">{value?.trim() || '—'}</span>
    </div>
  )
}

/** Collapse a path list into a one-line summary: first item + "+N more". */
function summarizePath(items: string[]): string | null {
  const clean = items.map(s => s?.trim()).filter(Boolean)
  if (clean.length === 0) return null
  if (clean.length === 1) return clean[0]
  return `${clean[0]} · +${clean.length - 1} more`
}
