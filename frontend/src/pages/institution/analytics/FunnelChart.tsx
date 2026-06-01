import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FunnelStage } from '../../../types'

const COBALT = '#2A6BD4'
const GOLD = '#FFD60A'
const COLORS = [COBALT, GOLD, '#22A06B', '#E6A020', '#6B7280']

const STAGE_LABELS: Record<string, string> = {
  impression: 'Impressions',
  view: 'Views',
  click: 'Clicks',
  save: 'Saves',
  compare: 'Compare',
  request_info: 'Request info',
  rsvp: 'RSVPs',
  attendance: 'Attendance',
  post_event_engagement: 'Post-event engagement',
  apply_started: 'Apps started',
  submitted: 'Submitted',
  decision_outcome: 'Decision outcome',
}

interface FunnelChartProps {
  stages: FunnelStage[]
  insufficient?: boolean
  empty?: boolean
}

export default function FunnelChart({ stages, insufficient, empty }: FunnelChartProps) {
  if (empty) {
    return (
      <p className="text-sm text-muted-foreground text-center py-10">
        No events match these filters.
      </p>
    )
  }

  if (insufficient) {
    return (
      <p className="text-sm text-muted-foreground text-center py-10">
        Not enough events in this window to plot.
      </p>
    )
  }

  const data = stages.map(s => ({
    name: STAGE_LABELS[s.stage] || s.stage.replace(/_/g, ' '),
    count: s.count,
    conversion: s.conversion_rate != null ? Math.round(s.conversion_rate * 100) : null,
  }))

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={Math.max(220, stages.length * 44)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
          <CartesianGrid stroke="hsl(var(--border))" strokeOpacity={0.5} horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="name"
            width={140}
            tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: number, _name, item) => {
              const conv = item.payload.conversion
              return conv != null ? [`${value} (${conv}% conv.)`, 'Count'] : [value, 'Count']
            }}
            contentStyle={{
              borderRadius: 8,
              border: '1px solid hsl(var(--border))',
              background: 'hsl(var(--card))',
            }}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={28}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="space-y-1">
        {stages.map(s => (
          <div key={s.stage} className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{STAGE_LABELS[s.stage] || s.stage}</span>
            <span className="font-semibold tabular-nums text-foreground">{s.count.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
