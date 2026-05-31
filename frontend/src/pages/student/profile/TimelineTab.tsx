/**
 * Profile → Timeline tab (spec 10 §14).
 * Chronological profile changes with source badges + filters.
 * Backed by the computed GET /students/me/timeline feed.
 */
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Milestone } from 'lucide-react'

import { getTimeline } from '../../../api/students'
import Card from '../../../components/ui/Card'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { EmptyHint, relativeTime } from './_shared'

const label = (item: any) => item.title || item.label || item.event || item.event_type || 'Update'

export default function TimelineTab() {
  const { data, isLoading } = useQuery<any[]>({ queryKey: ['timeline'], queryFn: getTimeline })
  const [filter, setFilter] = useState('all')

  const items = useMemo(() => {
    const list = Array.isArray(data) ? data : []
    return [...list].sort((a, b) => (b.date || '').localeCompare(a.date || ''))
  }, [data])

  const categories = useMemo(() => {
    const set = new Set<string>()
    items.forEach(i => set.add(i.event_type || i.section || 'other'))
    return ['all', ...Array.from(set)]
  }, [items])

  if (isLoading) return <div className="space-y-4"><SkeletonCard /></div>

  const shown = filter === 'all' ? items : items.filter(i => (i.event_type || i.section || 'other') === filter)

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <Milestone size={16} className="text-cobalt" />
          <h3 className="font-semibold text-charcoal">Timeline</h3>
        </div>
        {categories.length > 1 && (
          <select
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="text-sm border border-border rounded-lg px-2 py-1.5 bg-card text-charcoal capitalize"
          >
            {categories.map(c => (
              <option key={c} value={c}>{c === 'all' ? 'All sources' : c.replace(/_/g, ' ')}</option>
            ))}
          </select>
        )}
      </div>

      {shown.length === 0 ? (
        <EmptyHint>Nothing here yet. As you build your profile, changes appear on this timeline.</EmptyHint>
      ) : (
        <div className="relative pl-6 space-y-4">
          <div className="absolute left-[6px] top-1 bottom-1 w-px bg-student-mist" />
          {shown.map((item, i) => (
            <div key={i} className="relative">
              <div className="absolute -left-[18px] top-1 w-3 h-3 rounded-full bg-cobalt border-2 border-card" />
              <p className="text-sm font-medium text-charcoal">{label(item)}</p>
              <p className="text-xs text-slate">
                {item.date ? relativeTime(item.date) : ''}
                {(item.section || item.event_type) ? ` · ${(item.section || item.event_type).replace(/_/g, ' ')}` : ''}
              </p>
              {item.detail && <p className="text-xs text-slate mt-0.5">{item.detail}</p>}
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
