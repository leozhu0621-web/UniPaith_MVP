/**
 * Discover → Goal stack (rail widget for the Goals track).
 *
 * Read-only list of active SMART goals grouped by category. Live-updates as
 * Discovery extracts new goals. Manage-link sends to /s/profile?tab=goals.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ExternalLink, Target } from 'lucide-react'

import { listGoals } from '../../../api/goals'
import Card from '../../../components/ui/Card'
import type { GoalCategory, StudentGoal } from '../../../types'

const CATEGORIES: { key: GoalCategory; label: string }[] = [
  { key: 'academic', label: 'Academic' },
  { key: 'social', label: 'Social' },
  { key: 'personal', label: 'Personal' },
]

export default function GoalStackWidget() {
  const { data: goals = [], isLoading } = useQuery<StudentGoal[]>({
    queryKey: ['goals'],
    queryFn: () => listGoals('active'),
  })

  if (isLoading) {
    return <Card className="text-sm text-student-text">Loading…</Card>
  }

  if (goals.length === 0) {
    return (
      <Card className="text-sm text-student-text space-y-2">
        <div className="flex items-center gap-2 text-student-ink font-medium">
          <Target size={14} className="text-gold" />
          Goal stack
        </div>
        <p className="italic">
          As you talk through goals, I'll capture them as SMART rows here.
        </p>
      </Card>
    )
  }

  const grouped: Record<GoalCategory, StudentGoal[]> = {
    academic: [],
    social: [],
    personal: [],
  }
  for (const g of goals) grouped[g.category].push(g)

  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-student-ink font-medium text-sm">
          <Target size={14} className="text-gold" />
          Goal stack · {goals.length}
        </div>
        <Link
          to="/s/profile?tab=goals"
          className="text-xs text-student inline-flex items-center gap-1 hover:underline"
        >
          Manage <ExternalLink size={11} />
        </Link>
      </div>

      {CATEGORIES.map(c => {
        const items = grouped[c.key]
        if (items.length === 0) return null
        return (
          <div key={c.key}>
            <div className="text-[10px] uppercase tracking-wide text-student-text mb-1.5">
              {c.label} · {items.length}
            </div>
            <ul className="space-y-1">
              {items.slice(0, 4).map(g => (
                <li
                  key={g.id}
                  className="text-xs text-student-ink flex items-start gap-1.5"
                >
                  <span className="text-student-text mt-0.5">•</span>
                  <span className="line-clamp-2">{g.specific}</span>
                </li>
              ))}
              {items.length > 4 && (
                <li className="text-xs text-student-text">+{items.length - 4} more</li>
              )}
            </ul>
          </div>
        )
      })}
    </Card>
  )
}
