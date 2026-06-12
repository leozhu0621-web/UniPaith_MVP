import { useQuery } from '@tanstack/react-query'
import { TrendingDown } from 'lucide-react'
import Card from '../../../components/ui/Card'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'
import { getAnalyticsFunnel } from '../../../api/institutions'
import type { AnalyticsFilters, TopSource } from '../../../types'
import FunnelBars from './FunnelBars'

function TopSourceList({ title, sources }: { title: string; sources: TopSource[] }) {
  return (
    <Card pad={false} className="p-5">
      <p className="up-eyebrow mb-3">{title}</p>
      {sources.length === 0 ? (
        <p className="text-sm text-muted-foreground py-6 text-center">No activity in this window yet.</p>
      ) : (
        <ol className="space-y-2">
          {sources.map((s, i) => (
            <li key={`${s.source_kind}-${s.source_id ?? i}`} className="flex items-center gap-3">
              <span className="w-5 text-xs font-bold text-muted-foreground tabular-nums">{i + 1}</span>
              <span className="flex-1 min-w-0 truncate text-sm text-foreground">{s.label}</span>
              <span className="text-xs text-muted-foreground capitalize">{s.source_kind.replace(/_/g, ' ')}</span>
              <span className="w-12 text-right text-sm font-bold text-foreground tabular-nums">
                {s.action_count.toLocaleString()}
              </span>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

export default function FunnelTab({ filters }: { filters: AnalyticsFilters }) {
  const q = useQuery({
    queryKey: ['analytics-funnel', filters],
    queryFn: () => getAnalyticsFunnel(filters),
  })

  if (q.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-72" />
        <div className="grid lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      </div>
    )
  }

  if (q.isError || !q.data) {
    return <QueryError title="We couldn't load the funnel." onRetry={() => q.refetch()} />
  }

  const d = q.data

  if (!d.has_data) {
    return (
      <Card pad={false} className="p-10 text-center">
        <p className="text-sm text-muted-foreground">
          {filters.program_id ||
          filters.intake_id ||
          filters.segment_id ||
          filters.campaign_id ||
          filters.source_id
            ? 'No events match these filters.'
            : 'Not enough events in this window to plot.'}
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card pad={false} className="p-5">
        <p className="up-eyebrow mb-3">Recruitment funnel</p>
        <FunnelBars stages={d.stages} multicolor />
      </Card>

      {d.drop_off_alerts.length > 0 && (
        <div className="space-y-2">
          {d.drop_off_alerts.slice(0, 3).map((a, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded-lg bg-warning-soft text-warning p-4"
            >
              <TrendingDown size={18} className="mt-0.5 shrink-0" />
              <p className="text-sm">{a.hint}</p>
            </div>
          ))}
        </div>
      )}

      <div>
        <p className="up-eyebrow mb-3">Sub-funnels</p>
        <div className="grid lg:grid-cols-3 gap-4">
          {d.sub_funnels.map(sf => (
            <Card pad={false} key={sf.key} className="p-5">
              <p className="text-sm font-bold text-foreground mb-3">{sf.label}</p>
              <FunnelBars stages={sf.stages} height={sf.stages.length * 38} />
            </Card>
          ))}
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <TopSourceList title="Top content by clicks" sources={d.top_sources_by_clicks} />
        <TopSourceList title="Top content by apply started" sources={d.top_sources_by_apply_started} />
      </div>
    </div>
  )
}
