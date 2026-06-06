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
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'
import type { GoalCategory, StudentGoal } from '../../../types'

const CATEGORIES: { key: GoalCategory; label: string }[] = [
  { key: 'academic', label: 'Academic' },
  { key: 'social', label: 'Social' },
  { key: 'personal', label: 'Personal' },
]

export default function GoalStackWidget() {
  const { data: goals = [], isLoading, isError, refetch } = useQuery<StudentGoal[]>({
    queryKey: ['goals'],
    queryFn: () => listGoals('active'),
  })

  if (isLoading) {
    return (
      <Card className="space-y-3 p-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
        <Skeleton className="h-3 w-3/5" />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card className="space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium text-sm">
          <Target size={14} className="text-secondary" />
          Goal stack
        </div>
        <QueryError
          variant="inline"
          detail="Couldn't load your goals."
          onRetry={() => refetch()}
        />
      </Card>
    )
  }

  if (goals.length === 0) {
    return (
      <Card className="text-sm text-foreground space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium">
          <Target size={14} className="text-secondary" />
          Goal stack
        </div>
        <p className="text-muted-foreground">
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
        <div className="flex items-center gap-2 text-foreground font-medium text-sm">
          <Target size={14} className="text-secondary" />
          Goal stack · {goals.length}
        </div>
        <Link
          to="/s/profile?tab=goals"
          className="text-xs text-secondary inline-flex items-center gap-1 hover:underline"
        >
          Manage <ExternalLink size={11} />
        </Link>
      </div>

      {CATEGORIES.map(c => {
        const items = grouped[c.key]
        if (items.length === 0) return null
        return (
          <div key={c.key}>
            <div className="text-eyebrow uppercase text-muted-foreground mb-1.5">
              {c.label} · {items.length}
            </div>
            <ul className="space-y-1">
              {items.slice(0, 4).map(g => (
                <li
                  key={g.id}
                  className="text-xs text-foreground flex items-start gap-1.5"
                >
                  <span className="text-foreground mt-0.5">•</span>
                  <span className="line-clamp-2">{g.specific}</span>
                </li>
              ))}
              {items.length > 4 && (
                <li className="text-xs text-foreground">+{items.length - 4} more</li>
              )}
            </ul>
          </div>
        )
      })}
    </Card>
  )
}
