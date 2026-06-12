import { useQuery } from '@tanstack/react-query'
import Badge from '../../../components/ui/Badge'
import Card from '../../../components/ui/Card'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'
import { getAnalyticsAttribution } from '../../../api/institutions'
import { formatPercent } from '../../../utils/format'
import type { AnalyticsFilters } from '../../../types'

function pct(v: number | null): string {
  return v == null ? '—' : formatPercent(v)
}

export default function AttributionTab({ filters }: { filters: AnalyticsFilters }) {
  const q = useQuery({
    queryKey: ['analytics-attribution', filters],
    queryFn: () => getAnalyticsAttribution(filters),
  })

  if (q.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    )
  }

  if (q.isError || !q.data) {
    return <QueryError title="We couldn't load attribution." onRetry={() => q.refetch()} />
  }

  const d = q.data

  if (!d.has_data) {
    return (
      <Card pad={false} className="p-10 text-center">
        <p className="text-sm text-muted-foreground">
          {filters.program_id || filters.segment_id || filters.campaign_id
            ? 'No events match these filters.'
            : 'Not enough events in this window to plot.'}
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Campaign operational metrics (§6) */}
      <Card pad={false} className="p-5">
        <p className="up-eyebrow mb-3">Campaign performance</p>
        {d.campaigns.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">No sent campaigns in this window.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-2 pr-4 font-medium">Campaign</th>
                  <th className="py-2 px-2 font-medium">Channels</th>
                  <th className="py-2 px-2 text-right font-medium">Sent</th>
                  <th className="py-2 px-2 text-right font-medium">Delivered</th>
                  <th className="py-2 px-2 text-right font-medium">Opened</th>
                  <th className="py-2 px-2 text-right font-medium">Clicked</th>
                  <th className="py-2 pl-2 text-right font-medium">Apps started</th>
                </tr>
              </thead>
              <tbody>
                {d.campaigns.map(c => (
                  <tr key={c.campaign_id} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-medium text-foreground">{c.campaign_name}</td>
                    <td className="py-2 px-2 text-muted-foreground capitalize">
                      {c.channels.map(ch => ch.replace(/_/g, ' ')).join(', ') || '—'}
                    </td>
                    <td className="py-2 px-2 text-right tabular-nums text-foreground">{c.send_volume.toLocaleString()}</td>
                    <td className="py-2 px-2 text-right tabular-nums text-muted-foreground">
                      {c.delivered.toLocaleString()} <span className="text-xs">({pct(c.delivery_rate)})</span>
                    </td>
                    <td className="py-2 px-2 text-right tabular-nums text-muted-foreground">
                      {c.open_supported ? `${c.opened.toLocaleString()} (${pct(c.open_rate)})` : 'Not tracked'}
                    </td>
                    <td className="py-2 px-2 text-right tabular-nums text-muted-foreground">
                      {c.clicked.toLocaleString()} <span className="text-xs">({pct(c.click_rate)})</span>
                    </td>
                    <td className="py-2 pl-2 text-right">
                      <Badge variant={c.applications_started > 0 ? 'success' : 'neutral'}>
                        {c.applications_started}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Event operational metrics (§6) */}
      <Card pad={false} className="p-5">
        <p className="up-eyebrow mb-3">Event performance</p>
        {d.events.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">No events in this window.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="py-2 pr-4 font-medium">Event</th>
                  <th className="py-2 px-2 text-right font-medium">RSVPs</th>
                  <th className="py-2 px-2 text-right font-medium">Attended</th>
                  <th className="py-2 pl-2 text-right font-medium">Apps after</th>
                </tr>
              </thead>
              <tbody>
                {d.events.map(e => (
                  <tr key={e.event_id} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-medium text-foreground">{e.event_name}</td>
                    <td className="py-2 px-2 text-right tabular-nums text-foreground">{e.rsvps.toLocaleString()}</td>
                    <td className="py-2 px-2 text-right tabular-nums text-muted-foreground">
                      {e.attended.toLocaleString()} <span className="text-xs">({pct(e.attendance_rate)})</span>
                    </td>
                    <td className="py-2 pl-2 text-right">
                      <Badge variant={e.applications_after > 0 ? 'success' : 'neutral'}>
                        {e.applications_after}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Top content (§4) */}
      <div className="grid lg:grid-cols-2 gap-4">
        <Card pad={false} className="p-5">
          <p className="up-eyebrow mb-3">Top content by clicks</p>
          {d.top_content_by_clicks.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">No clicks in this window.</p>
          ) : (
            <ol className="space-y-2">
              {d.top_content_by_clicks.map((c, i) => (
                <li key={`${c.source_kind}-${c.source_id ?? i}`} className="flex items-center gap-3">
                  <span className="w-5 text-xs font-bold text-muted-foreground tabular-nums">{i + 1}</span>
                  <span className="flex-1 min-w-0 truncate text-sm text-foreground">{c.title}</span>
                  <span className="text-xs text-muted-foreground capitalize">{c.source_kind.replace(/_/g, ' ')}</span>
                  <span className="w-12 text-right text-sm font-bold text-foreground tabular-nums">{c.clicks}</span>
                </li>
              ))}
            </ol>
          )}
        </Card>
        <Card pad={false} className="p-5">
          <p className="up-eyebrow mb-3">Top content by apply started</p>
          {d.top_content_by_apply_started.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">No apply-starts in this window.</p>
          ) : (
            <ol className="space-y-2">
              {d.top_content_by_apply_started.map((c, i) => (
                <li key={`${c.source_kind}-${c.source_id ?? i}`} className="flex items-center gap-3">
                  <span className="w-5 text-xs font-bold text-muted-foreground tabular-nums">{i + 1}</span>
                  <span className="flex-1 min-w-0 truncate text-sm text-foreground">{c.title}</span>
                  <span className="text-xs text-muted-foreground capitalize">{c.source_kind.replace(/_/g, ' ')}</span>
                  <span className="w-12 text-right text-sm font-bold text-foreground tabular-nums">{c.apply_started}</span>
                </li>
              ))}
            </ol>
          )}
        </Card>
      </div>
    </div>
  )
}
