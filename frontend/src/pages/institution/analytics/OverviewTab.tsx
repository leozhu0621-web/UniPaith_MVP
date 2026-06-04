import { useQuery } from '@tanstack/react-query'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Card from '../../../components/ui/Card'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'
import { getAnalyticsOverview } from '../../../api/institutions'
import type { AnalyticsFilters, KpiMetric } from '../../../types'
import { AXIS_TICK, CHART, formatDelta, formatKpi, GRID_STROKE, TOOLTIP_STYLE, titleCase } from './constants'

// Institution surfaces stay on the cobalt/neutral palette (no gold). Decisions
// read by semantic intent: admit=green, reject=amber, waitlist=neutral, defer=cobalt.
const DECISION_COLORS: Record<string, string> = {
  admitted: CHART.green,
  rejected: CHART.amber,
  denied: CHART.amber,
  waitlisted: CHART.muted,
  deferred: CHART.cobalt,
}

function KpiCard({
  label,
  metric,
  timeWindow,
}: {
  label: string
  metric: KpiMetric
  timeWindow: string | undefined
}) {
  const delta = formatDelta(metric.delta_pct, timeWindow)
  return (
    <Card className="p-5">
      <p className="up-eyebrow">{label}</p>
      <p className="mt-2 text-h2 font-bold text-foreground tabular-nums">
        {formatKpi(metric.value, metric.unit)}
      </p>
      <p className={`mt-1 text-xs tabular-nums ${delta ? delta.tone : 'text-muted-foreground'}`}>
        {delta ? delta.text : 'No prior-period comparison'}
      </p>
    </Card>
  )
}

function ChartEmpty({ hint }: { hint: string }) {
  return <p className="text-sm text-muted-foreground py-10 text-center">{hint}</p>
}

export default function OverviewTab({ filters }: { filters: AnalyticsFilters }) {
  const q = useQuery({
    queryKey: ['analytics-overview', filters],
    queryFn: () => getAnalyticsOverview(filters),
  })

  if (q.isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <div className="grid lg:grid-cols-2 gap-4">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    )
  }

  if (q.isError || !q.data) {
    return <QueryError title="We couldn't load analytics." onRetry={() => q.refetch()} />
  }

  const d = q.data
  const tw = filters.time_window
  const overTime = d.apps_over_time.map(p => ({ period: p.period.slice(5), count: p.count }))
  const byProgram = d.apps_by_program
  const byStatus = Object.entries(d.apps_by_status)
    .map(([k, v]) => ({ name: titleCase(k), count: v }))
    .sort((a, b) => b.count - a.count)
  const decisions = Object.entries(d.decisions_breakdown).map(([k, v]) => ({ key: k, name: titleCase(k), count: v }))

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        <KpiCard label="Total applications" metric={d.total_applications} timeWindow={tw} />
        <KpiCard label="Acceptance rate" metric={d.acceptance_rate} timeWindow={tw} />
        <KpiCard label="Avg match" metric={d.avg_match_score} timeWindow={tw} />
        <KpiCard label="Yield" metric={d.yield_rate} timeWindow={tw} />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <p className="up-eyebrow mb-3">Applications over time</p>
          {overTime.length < 2 ? (
            <ChartEmpty hint="Not enough events in this window to plot." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={overTime} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="appsFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={CHART.cobalt} stopOpacity={0.25} />
                    <stop offset="100%" stopColor={CHART.cobalt} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={GRID_STROKE} strokeOpacity={0.5} vertical={false} />
                <XAxis dataKey="period" tick={AXIS_TICK} tickLine={false} axisLine={false} />
                <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="count" stroke={CHART.cobalt} strokeWidth={2} fill="url(#appsFill)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card className="p-5">
          <p className="up-eyebrow mb-3">Applications by program</p>
          {byProgram.length === 0 ? (
            <ChartEmpty hint="No applications match these filters." />
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(160, byProgram.length * 36)}>
              <BarChart layout="vertical" data={byProgram} margin={{ top: 4, right: 32, left: 8, bottom: 0 }}>
                <CartesianGrid stroke={GRID_STROKE} strokeOpacity={0.5} horizontal={false} />
                <XAxis type="number" tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} />
                <YAxis type="category" dataKey="label" width={120} tick={{ fontSize: 11, fill: 'hsl(var(--foreground))' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }} />
                <Bar dataKey="count" fill={CHART.cobalt} radius={[0, 4, 4, 0]} maxBarSize={22} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card className="p-5">
          <p className="up-eyebrow mb-3">Applications by status</p>
          {byStatus.length === 0 ? (
            <ChartEmpty hint="No applications match these filters." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={byStatus} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke={GRID_STROKE} strokeOpacity={0.5} vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} tickLine={false} axisLine={false} interval={0} angle={-20} textAnchor="end" height={48} />
                <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }} />
                <Bar dataKey="count" fill={CHART.cobalt} radius={[4, 4, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card className="p-5">
          <p className="up-eyebrow mb-3">Decisions breakdown</p>
          {decisions.length === 0 ? (
            <ChartEmpty hint="No decisions in this window yet." />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={decisions} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke={GRID_STROKE} strokeOpacity={0.5} vertical={false} />
                <XAxis dataKey="name" tick={AXIS_TICK} tickLine={false} axisLine={false} />
                <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
                  {decisions.map(item => (
                    <Cell key={item.key} fill={DECISION_COLORS[item.key] ?? CHART.muted} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>
    </div>
  )
}
