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
import type { MaslowLevel, StudentNeed } from '../../../types'

const TIERS: { key: MaslowLevel; label: string }[] = [
  { key: 'self_actualization', label: 'Self-actualization' },
  { key: 'self_esteem', label: 'Self-esteem' },
  { key: 'social', label: 'Social' },
  { key: 'safety', label: 'Safety' },
  { key: 'physiological', label: 'Physiological' },
]

export default function NeedsMapWidget() {
  const { data: needs = [], isLoading } = useQuery<StudentNeed[]>({
    queryKey: ['needs'],
    queryFn: () => listNeeds(),
  })

  if (isLoading) {
    return <Card className="text-sm text-student-text">Loading…</Card>
  }

  if (needs.length === 0) {
    return (
      <Card className="text-sm text-student-text space-y-2">
        <div className="flex items-center gap-2 text-student-ink font-medium">
          <Heart size={14} className="text-gold" />
          Needs map
        </div>
        <p className="italic">
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
        <div className="flex items-center gap-2 text-student-ink font-medium text-sm">
          <Heart size={14} className="text-gold" />
          Needs map · {needs.length}
        </div>
        <Link
          to="/s/profile?tab=needs"
          className="text-xs text-student inline-flex items-center gap-1 hover:underline"
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
                  ? 'border-student/30 bg-student/5'
                  : 'border-divider bg-transparent',
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span
                  className={clsx(
                    'text-xs font-medium',
                    isFilled ? 'text-student-ink' : 'text-student-text',
                  )}
                >
                  {tier.label}
                </span>
                <span className="text-[10px] text-student-text">
                  {items.length}
                  {mustHaves > 0 && (
                    <span className="ml-1.5 text-destructive">• {mustHaves} must-have</span>
                  )}
                </span>
              </div>
              {items.length > 0 && (
                <div className="mt-1 text-[11px] text-student-text line-clamp-1">
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
