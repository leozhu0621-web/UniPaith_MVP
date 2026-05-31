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
  ChevronDown,
  ChevronRight,
  Compass,
  Pencil,
  Sparkles,
  Target,
} from 'lucide-react'

import { listGoals } from '../../../api/goals'
import { generateStrategy, getActiveStrategy } from '../../../api/strategy'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Card from '../../../components/ui/Card'
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

  const { data: strategy, isLoading: strategyLoading } = useQuery<StudentStrategy | null>({
    queryKey: ['strategy', 'active'],
    queryFn: () => getActiveStrategy(),
  })
  // Only fetch goals when there's no active strategy — saves a roundtrip
  // on the happy path.
  const { data: goals = [] } = useQuery<StudentGoal[]>({
    queryKey: ['goals', 'active'],
    queryFn: () => listGoals('active'),
    enabled: !strategy,
  })

  const generateMut = useMutation({
    mutationFn: () => generateStrategy(),
    onSuccess: () => {
      showToast('Draft strategy generated. Activate from Profile.', 'success')
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

  if (strategyLoading) return null

  // State 1 — no goals at all → push student back to Discover.
  if (!strategy && goals.length === 0) {
    return (
      <Card className="bg-student/5 border-student/30">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <Compass size={18} className="text-student mt-0.5 shrink-0" />
            <div>
              <div className="text-sm font-medium text-student-ink">
                Tell me about you first.
              </div>
              <div className="text-xs text-student-text mt-1 max-w-2xl">
                Match works against the broad strategy you build in Discover. Talk through your
                goals and I'll surface the strategy here once you have at least one active
                academic goal.
              </div>
            </div>
          </div>
          <Link to="/s">
            <Button size="sm">Open Discover</Button>
          </Link>
        </div>
      </Card>
    )
  }

  // State 2 — goals exist but no active strategy → offer to generate.
  if (!strategy) {
    return (
      <Card className="bg-student/5 border-student/30">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <Sparkles size={18} className="text-gold mt-0.5 shrink-0" />
            <div>
              <div className="text-sm font-medium text-student-ink">
                Ready to plan your strategy.
              </div>
              <div className="text-xs text-student-text mt-1">
                You have {goals.length} active goal{goals.length === 1 ? '' : 's'}. Generate a
                draft strategy now and review/activate it from your profile.
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

  // State 3 — active strategy.
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <button
          className="flex items-center gap-2 text-left"
          onClick={toggle}
          aria-expanded={!collapsed}
        >
          {collapsed ? (
            <ChevronRight size={14} className="text-student-text" />
          ) : (
            <ChevronDown size={14} className="text-student-text" />
          )}
          <Target size={16} className="text-student" />
          <div>
            <div className="text-xs uppercase tracking-wide text-student-text">
              Active strategy · v{strategy.version}
            </div>
            <div className="text-base font-semibold text-student-ink">
              {strategy.career_target ?? 'Strategy'}
              {strategy.target_degree && (
                <span className="text-sm text-student-text font-normal">
                  {' '}
                  → {strategy.target_degree}
                </span>
              )}
            </div>
          </div>
        </button>
        <div className="flex items-center gap-2 shrink-0">
          {strategy.is_stub && (
            <Badge variant="warning" size="sm" className="inline-flex items-center gap-1">
              <Sparkles size={10} />
              preview
            </Badge>
          )}
          <Link to="/s/profile?tab=strategy">
            <Button size="sm" variant="ghost">
              <Pencil size={13} className="mr-1" />
              Edit
            </Button>
          </Link>
        </div>
      </div>

      {!collapsed && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <PathCol
            title="Academic"
            count={strategy.academic_path.length}
            items={strategy.academic_path.map(s => s.step)}
          />
          <PathCol
            title="Financial"
            count={strategy.financial_path.length}
            items={strategy.financial_path.map(f => f.aid_type)}
          />
          <PathCol
            title="Geographic"
            count={strategy.geographic_path.length}
            items={strategy.geographic_path.map(g => g.region)}
          />
        </div>
      )}
    </Card>
  )
}

function PathCol({
  title,
  count,
  items,
}: {
  title: string
  count: number
  items: string[]
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-student-text mb-1.5">
        {title} · {count}
      </div>
      <ul className="space-y-1">
        {items.slice(0, 4).map((s, i) => (
          <li key={i} className="text-xs text-student-ink flex items-start gap-1.5">
            <span className="text-student-text mt-0.5">•</span>
            <span className="line-clamp-2">{s}</span>
          </li>
        ))}
        {items.length > 4 && (
          <li className="text-xs text-student-text">+{items.length - 4} more</li>
        )}
      </ul>
    </div>
  )
}
