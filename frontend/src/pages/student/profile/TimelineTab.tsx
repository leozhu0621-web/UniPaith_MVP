/**
 * Profile → Timeline tab (Spec/08 §14).
 * Chronological profile + application milestones with source badges + filter.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import Badge from '../../../components/ui/Badge'
import Card from '../../../components/ui/Card'
import EmptyState from '../../../components/ui/EmptyState'
import Select from '../../../components/ui/Select'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { getTimeline } from '../../../api/students'
import { formatDate } from '../../../utils/format'
import { SectionHeader } from './shared'

type Source = 'profile' | 'application' | 'decision' | 'account'

function sourceOf(eventType: string): Source {
  if (eventType.startsWith('application')) return 'application'
  if (eventType.startsWith('decision')) return 'decision'
  if (eventType === 'profile_created') return 'account'
  return 'profile'
}

const SOURCE_LABEL: Record<Source, string> = {
  profile: 'Profile',
  application: 'Application',
  decision: 'Decision',
  account: 'Account',
}
const SOURCE_VARIANT: Record<Source, 'info' | 'success' | 'warning' | 'neutral'> = {
  profile: 'info',
  application: 'neutral',
  decision: 'success',
  account: 'warning',
}

export default function TimelineTab() {
  const { data: timeline, isLoading } = useQuery({ queryKey: ['timeline'], queryFn: getTimeline, retry: false })
  const [filter, setFilter] = useState<string>('')

  const items = useMemo(() => {
    const list: any[] = Array.isArray(timeline) ? timeline : []
    const withSource = list.map(i => ({ ...i, source: sourceOf(i.event_type) }))
    withSource.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    return filter ? withSource.filter(i => i.source === filter) : withSource
  }, [timeline, filter])

  if (isLoading) return <div className="space-y-3"><SkeletonCard /><SkeletonCard /></div>

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Timeline"
        description="Every meaningful change to your record, newest first."
        action={
          <div className="w-44">
            <Select
              uiSize="sm"
              placeholder="All sources"
              options={[
                { value: 'profile', label: 'Profile' },
                { value: 'application', label: 'Applications' },
                { value: 'decision', label: 'Decisions' },
                { value: 'account', label: 'Account' },
              ]}
              value={filter}
              onChange={e => setFilter(e.target.value)}
            />
          </div>
        }
      />

      {items.length === 0 ? (
        <EmptyState
          title="Nothing here yet"
          description="Your timeline fills in as you complete sections, upload documents, and move applications forward."
        />
      ) : (
        <Card className="p-5">
          <ol className="relative pl-6">
            <span className="absolute left-[7px] top-1 bottom-1 w-px bg-border" aria-hidden="true" />
            {items.map((item, i) => (
              <li key={i} className="relative pb-5 last:pb-0">
                <span
                  className={`absolute -left-[19px] top-1 h-3.5 w-3.5 rounded-full ring-2 ring-card ${item.source === 'decision' ? 'bg-primary' : 'bg-secondary'}`}
                  aria-hidden="true"
                />
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">{item.label}</p>
                    {item.detail && <p className="text-xs text-muted-foreground mt-0.5">{item.detail}</p>}
                    <p className="text-xs text-muted-foreground mt-0.5">{formatDate(item.date)}</p>
                  </div>
                  <Badge variant={SOURCE_VARIANT[item.source as Source]}>{SOURCE_LABEL[item.source as Source]}</Badge>
                </div>
              </li>
            ))}
          </ol>
        </Card>
      )}
    </div>
  )
}
