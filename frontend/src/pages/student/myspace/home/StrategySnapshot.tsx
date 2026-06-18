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
