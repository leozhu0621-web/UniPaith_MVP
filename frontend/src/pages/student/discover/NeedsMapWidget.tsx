/**
 * Discover → Needs map (rail widget for the Needs track).
 *
 * Maslow pyramid rendered top-down (self-actualization first — that's where
 * the differentiating signal sits per spec). Each tier shows a count and
 * the most-recent must-have items.
 */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ExternalLink, Heart } from 'lucide-react'
import clsx from 'clsx'

import { listNeeds } from '../../../api/needs'
import Card from '../../../components/ui/Card'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'
import type { MaslowLevel, StudentNeed } from '../../../types'

const TIERS: { key: MaslowLevel; label: string }[] = [
  { key: 'self_actualization', label: 'Self-actualization' },
  { key: 'self_esteem', label: 'Self-esteem' },
  { key: 'social', label: 'Social' },
  { key: 'safety', label: 'Safety' },
  { key: 'physiological', label: 'Physiological' },
]

export default function NeedsMapWidget() {
  const { data: needs = [], isLoading, isError, refetch } = useQuery<StudentNeed[]>({
    queryKey: ['needs'],
    queryFn: () => listNeeds(),
  })

  if (isLoading) {
    return (
      <Card pad={false} className="space-y-3 p-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </Card>
    )
  }

  if (isError) {
    return (
      <Card className="space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium text-sm">
          <Heart size={14} className="text-secondary" />
          Needs map
        </div>
        <QueryError
          variant="inline"
          detail="Couldn't load your needs map."
          onRetry={() => refetch()}
        />
      </Card>
    )
  }

  if (needs.length === 0) {
    return (
      <Card className="text-sm text-foreground space-y-2">
        <div className="flex items-center gap-2 text-foreground font-medium">
          <Heart size={14} className="text-secondary" />
          Needs map
        </div>
        <p className="text-muted-foreground">
          As we talk through what you can't do without, I'll classify it on Maslow's hierarchy.
        </p>
      </Card>
    )
  }

  const grouped: Record<MaslowLevel, StudentNeed[]> = {
    physiological: [],
    safety: [],
    social: [],
    self_esteem: [],
    self_actualization: [],
  }
  for (const n of needs) grouped[n.maslow_level].push(n)

  return (
    <Card className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-foreground font-medium text-sm">
          <Heart size={14} className="text-secondary" />
          Needs map · {needs.length}
        </div>
        <Link
          to="/s/profile?tab=needs"
          className="text-xs text-secondary inline-flex items-center gap-1 hover:underline"
        >
          Manage <ExternalLink size={11} />
        </Link>
      </div>

      <div className="space-y-1">
        {TIERS.map(tier => {
          const items = grouped[tier.key]
          const isFilled = items.length > 0
          const mustHaves = items.filter(n => n.severity === 'must_have').length
          return (
            <div
              key={tier.key}
              className={clsx(
                'rounded border px-2.5 py-1.5 transition-colors',
                isFilled
                  ? 'border-secondary/30 bg-secondary/5'
                  : 'border-border bg-transparent',
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium text-foreground">
                  {tier.label}
                </span>
                <span className="text-[10px] text-foreground">
                  {items.length}
                  {mustHaves > 0 && (
                    <span className="ml-1.5 text-foreground">• {mustHaves} must-have</span>
                  )}
                </span>
              </div>
              {items.length > 0 && (
                <div className="mt-1 text-[11px] text-foreground line-clamp-1">
                  {items
                    .slice(0, 2)
                    .map(n => n.need_type)
                    .join(' · ')}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
